import mysql.connector
from mysql.connector import Error

# Function to connect to MySQL
def create_connection():
    try:
        # Establishing the connection
        connection = mysql.connector.connect(
            host='localhost',    # MySQL host (use 'localhost' if running locally)
            user='username',         # MySQL username
            password='Gern@8280',  # MySQL root password
            database='my_database'   # The database to connect to (change as needed)
        )
        if connection.is_connected():
            print("Successfully connected to MySQL")
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

# Function to create a table
def create_table(connection):
    try:
        cursor = connection.cursor()
        # SQL query to create a new table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS employees (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            age INT,
            department VARCHAR(50)
        );
        """
        cursor.execute(create_table_query)
        print("Table created successfully")
    except Error as e:
        print(f"Error creating table: {e}")

# Function to insert data into the table
def insert_data(connection):
    try:
        cursor = connection.cursor()
        insert_query = "INSERT INTO employees (name, age, department) VALUES (%s, %s, %s)"
        values = [
            ('Alice', 30, 'HR'),
            ('Bob', 25, 'Engineering'),
            ('Charlie', 35, 'Sales')
        ]
        cursor.executemany(insert_query, values)
        connection.commit()
        print(f"{cursor.rowcount} rows inserted successfully")
    except Error as e:
        print(f"Error inserting data: {e}")

# Function to fetch data from the table
def fetch_data(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM employees")
        rows = cursor.fetchall()
        print("Data from employees table:")
        for row in rows:
            print(row)
    except Error as e:
        print(f"Error fetching data: {e}")

# Function to update data in the table
def update_data(connection):
    try:
        cursor = connection.cursor()
        update_query = "UPDATE employees SET age = %s WHERE name = %s"
        values = (40, 'Alice')
        cursor.execute(update_query, values)
        connection.commit()
        print(f"{cursor.rowcount} row(s) updated successfully")
    except Error as e:
        print(f"Error updating data: {e}")

# Function to delete data from the table
def delete_data(connection):
    try:
        cursor = connection.cursor()
        delete_query = "DELETE FROM employees WHERE name = %s"
        cursor.execute(delete_query, ('Bob',))
        connection.commit()
        print(f"{cursor.rowcount} row(s) deleted successfully")
    except Error as e:
        print(f"Error deleting data: {e}")

# Main function to execute the operations
def main():
    # Step 1: Create a connection to MySQL
    connection = create_connection()

    if connection:
        # Step 2: Create table
        create_table(connection)

        # Step 3: Insert data into table
        insert_data(connection)

        # Step 4: Fetch and display data from the table
        fetch_data(connection)

        # Step 5: Update data in the table
        update_data(connection)

        # Step 6: Delete data from the table
        delete_data(connection)

        # Step 7: Fetch and display data again to see the changes
        fetch_data(connection)

        # Close the connection
        connection.close()

if __name__ == "__main__":
    main()
