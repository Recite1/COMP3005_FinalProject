import psycopg2

#Connect to the db
def get_connection():
    """
    Returns a connection to the database.
    """
    connection = psycopg2.connect(
            dbname='FinalProject',
            user='postgres',
            password='1234',
            host='localhost',
            port='5433'
        )
    print("Connected to database FinalProject")
    return connection

def remove_connection(connection):
    connection.close()
