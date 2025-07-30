# Database Data Migrator

## Project Description
This is a Python project designed to migrate documents table from a SQL Server database to a MySQL database while uploading document files to Azure Blob Storage. The migration script handles hex-encoded binary data conversion and maintains document metadata across different storage systems.

## Project Structure
```
db-data-migrator/
├── src/
│   └── main.py          # Main migration application
├── tests/
│   └── test_main.py     # Unit tests for main.py
├── .env                 # Environment variables (not tracked by git)
├── .env.example         # Template for environment variables
├── requirements.txt     # Project dependencies
├── .gitignore          # Files and directories to ignore by Git
└── README.md           # Project documentation
```

## Requirements
Make sure you have Python 3.7+ installed on your system. You can install the project dependencies using the following command:

```bash
pip install -r requirements.txt
```

### Required Dependencies:
- `pyodbc` - SQL Server database connectivity
- `mysql-connector-python` - MySQL database connectivity
- `azure-storage-blob` - Azure Blob Storage client
- `python-dotenv` - Environment variable management

## Configuration
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your actual database credentials:
   ```
   # SQL Server Configuration
   SQLSERVER_DRIVER=ODBC Driver 17 for SQL Server
   SQLSERVER_SERVER=your_sql_server_host
   SQLSERVER_DATABASE=your_database_name
   SQLSERVER_UID=your_username
   SQLSERVER_PWD=your_password

   # MySQL Configuration
   MYSQL_HOST=your_mysql_host
   MYSQL_USER=your_mysql_user
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=your_mysql_database

   # Azure Blob Storage Configuration
   AZURE_STORAGE_CONNECTION_STRING=your_azure_connection_string
   AZURE_CONTAINER_NAME=your_container_name
   ```

## Database Setup
Ensure your MySQL database has the required table structure:

```sql
CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    description TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    isDeleted TINYINT DEFAULT 0
);
```

## Execution
To run the migration application, use the following command:

```bash
python src/main.py
```

The migration process will:
1. Connect to the source SQL Server database
2. Query documents from the TDOCUMENT table (excluding deleted records)
3. Decode hex-encoded binary data from Document_obj field
4. Upload files to Azure Blob Storage in the 'documents' folder
5. Insert document metadata into the MySQL database

## Testing
To run the unit tests, you can use the following command:

```bash
python -m unittest tests/test_main.py
```

Or run all tests in the tests directory:

```bash
python -m pytest tests/
```

## Features
- **Robust error handling**: Continues processing even if individual documents fail
- **Progress tracking**: Logs migration progress with detailed status information
- **Data validation**: Handles different Document_obj data types (bytes/string)
- **Secure configuration**: Uses environment variables for sensitive credentials
- **Azure integration**: Uploads files with appropriate content types

## Security Notes
- Never commit the `.env` file to version control
- The `.env` file contains sensitive database credentials
- Use the `.env.example` as a template for team members
- Ensure proper access controls on your databases and Azure storage

## Troubleshooting
Common issues and solutions:

1. **SQL Server connection issues**: Verify ODBC driver installation and connection string
2. **MySQL connection problems**: Check host, port, and credential configuration
3. **Azure storage errors**: Validate connection string and container permissions
4. **Hex decoding failures**: Some documents may have corrupted or invalid hex data

## Contributions
Contributions are welcome. If you want to contribute, please open an issue or submit a pull request.

## Future upgrades 
This project could also be use to migrate metadata from multiples tables between SQL Server en MySQL databases with just a couple of changes at code level.