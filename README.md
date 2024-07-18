# PTAnalyser

PTAnalyser is a web application built with Python and Flask. It is designed to provide sensitive information about IT companies in Portugal. The application allows users to execute SQL queries to discover information such as company name, website, rating, and more.

## Features

- User authentication system (login/logout)
- SQL query execution
- Admin page for managing companies
- Web scraping capabilities for updating company information

## Technologies Used

- Python
- Flask
- MySQL
- HTML/CSS/Bootstrap

## Setup

To run this project, you need to have Python and Flask installed on your system. 

1. Clone the repository to your local machine.
2. Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

3. Run the application:

## Configuration
Database configuration details are stored in config.py. Update these details according to your MySQL server setup.

```commandline
mysql_database_user = "YourUsername"
mysql_database_user_password = "YourPassword"
mysql_database_name = "YourDatabaseName"
mysql_database_host = "YourDatabaseHost"
```

## Usage

After running the application, navigate to `http://localhost:5000` in your web browser.

- To login, navigate to `http://localhost:5000/login`.
- To logout, navigate to `http://localhost:5000/logout`.
- To execute SQL queries, login and navigate to `http://localhost:5000/queryUser`.
- To manage companies, login as an admin and navigate to `http://localhost:5000/adminPage`.

## Note

This application is for educational purposes only. Please ensure you have the necessary permissions before scraping or accessing data.