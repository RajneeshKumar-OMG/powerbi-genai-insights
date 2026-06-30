from snowflake_writer import get_snowflake_connection

conn = get_snowflake_connection()

cursor = conn.cursor()

cursor.execute("SELECT CURRENT_USER(), CURRENT_DATABASE(), CURRENT_SCHEMA()")

print(cursor.fetchone())

cursor.close()
conn.close()