import pyodbc
import mysql.connector
from azure.storage.blob import BlobServiceClient, ContentSettings
import binascii
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def migrate_documents(
    sqlserver_conn_str,
    mysql_conn_params,
    azure_conn_str,
    container_name
):
    try:
        logging.info("Connecting to SQL Server...")
        sql_conn = pyodbc.connect(sqlserver_conn_str)
        sql_cursor = sql_conn.cursor()
        logging.info("SQL Server connection established.")
    except Exception as e:
        logging.error(f"Error connecting to SQL Server: {e}")
        return

    try:
        sql_cursor.execute(
            "SELECT Document_nbr, Document_nm, Document_obj, Document_Short_desc, Document_Type_nm, Created_On_ts, Last_Modified_On_ts, Deleted_fg FROM DOAPOA_Prod.dbo.TDOCUMENT WHERE Deleted_fg = 0"
        )
        rows = sql_cursor.fetchall()
        logging.info(f"Retrieved {len(rows)} documents from the old database.")
    except Exception as e:
        logging.error(f"Error querying documents in SQL Server: {e}")
        sql_cursor.close()
        sql_conn.close()
        return

    try:
        logging.info("Connecting to MySQL...")
        mysql_conn = mysql.connector.connect(**mysql_conn_params)
        mysql_cursor = mysql_conn.cursor()
        logging.info("MySQL connection established.")
    except Exception as e:
        logging.error(f"Error connecting to MySQL: {e}")
        sql_cursor.close()
        sql_conn.close()
        return

    try:
        logging.info("Connecting to Azure Blob Storage...")
        blob_service_client = BlobServiceClient.from_connection_string(azure_conn_str)
        container_client = blob_service_client.get_container_client(container_name)
        logging.info("Azure Blob Storage connection established.")
    except Exception as e:
        logging.error(f"Error connecting to Azure Blob Storage: {e}")
        sql_cursor.close()
        sql_conn.close()
        mysql_cursor.close()
        mysql_conn.close()
        return

    for idx, row in enumerate(rows, 1):
        file_name = row.Document_nm
        file_type = row.Document_Type_nm
        description = row.Document_Short_desc
        created_at = row.Created_On_ts
        updated_at = row.Last_Modified_On_ts
        is_deleted = int(row.Deleted_fg)
        doc_obj = row.Document_obj

        # Robust hex to binary decoding
        try:
            if isinstance(doc_obj, bytes):
                hex_str = doc_obj.hex()
                if hex_str.startswith('0x'):
                    hex_str = hex_str[2:]
                file_content = binascii.unhexlify(hex_str)
            elif isinstance(doc_obj, str):
                hex_str = doc_obj[2:] if doc_obj.startswith('0x') else doc_obj
                file_content = binascii.unhexlify(hex_str)
            else:
                raise ValueError("Unexpected type for Document_obj")
        except Exception as e:
            logging.error(f"[{idx}/{len(rows)}] Error decoding file '{file_name}': {e}")
            continue

        # Upload file to Azure Blob Storage in the 'documents' folder
        blob_path = f"documents/{file_name}"
        blob_client = container_client.get_blob_client(blob_path)
        try:
            blob_client.upload_blob(
                file_content,
                overwrite=True,
                content_settings=ContentSettings(content_type=file_type)
            )
        except Exception as e:
            logging.error(
                f"[{idx}/{len(rows)}] NOT UPLOADED: '{file_name}' | Type: '{file_type}' | Desc: '{description}' | Error: {e}"
            )
            continue

        # Insert metadata into the new database
        try:
            mysql_cursor.execute(
                "INSERT INTO documents (file_name, file_type, description, created_at, updated_at, isDeleted) VALUES (%s, %s, %s, %s, %s, %s)",
                (file_name, file_type, description, created_at, updated_at, is_deleted)
            )
            mysql_conn.commit()
        except Exception as e:
            logging.error(f"Error inserting metadata for '{file_name}' into database: {e}")

    sql_cursor.close()
    sql_conn.close()
    mysql_cursor.close()
    mysql_conn.close()
    logging.info("Migration completed.")

def main():
    # Load credentials from environment variables
    sqlserver_conn_str = (
        f"DRIVER={{{os.getenv('SQLSERVER_DRIVER')}}};"
        f"SERVER={os.getenv('SQLSERVER_SERVER')};"
        f"DATABASE={os.getenv('SQLSERVER_DATABASE')};"
        f"UID={os.getenv('SQLSERVER_UID')};"
        f"PWD={os.getenv('SQLSERVER_PWD')}"
    )
    
    mysql_conn_params = {
        'host': os.getenv('MYSQL_HOST'),
        'user': os.getenv('MYSQL_USER'),
        'password': os.getenv('MYSQL_PASSWORD'),
        'database': os.getenv('MYSQL_DATABASE')
    }
    
    azure_conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    container_name = os.getenv('AZURE_CONTAINER_NAME')

    migrate_documents(sqlserver_conn_str, mysql_conn_params, azure_conn_str, container_name)

if __name__ == "__main__":
    main()