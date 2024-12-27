import pymysql

# Database connection details
host = "185.214.132.9"
database = "u427431418_his_price"
user = "u427431418_cfa187260"
password = "Gern@8280"

try:
    # Establishing the connection
    connection = pymysql.connect(
        host=host,
        database=database,
        user=user,
        password=password
    )

    # Create a cursor object
    cursor = connection.cursor()

    # Execute a query (example: Show databases)
    cursor.execute("SHOW DATABASES;")
    databases = cursor.fetchall()

    # Print the results
    for db in databases:
        print(db)

except pymysql.MySQLError as e:
    print(f"Error: {e}")

finally:
    if connection.open:
        cursor.close()
        connection.close()
        print("Connection closed.")
