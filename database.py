import psycopg2

<<<<<<< HEAD
def add_refers_to_database(refers_value: str):
    conn = psycopg2.connect("dbname=taqsir user=postgres password=abdulaziztaqsir")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE refer (
            id SERIAL PRIMARY KEY,
            refers TEXT
        );
        """)

    cur.execute(
        "INSERT INTO refer (refers) VALUES (%s);",
        (refers_value,)
    )

    conn.commit()
    cur.close()
    conn.close()

add_refers_to_database("taqsir")

=======
conn = psycopg2.connect("dbname=pdpschool user=postgres password=abdulaziztaqsir")


cur = conn.cursor()
# cur.execute("CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar(30));")
cur.execute("INSERT INTO test(num, data) values (20, 'va alaykum assalom');")

conn.commit()
cur.close()
conn.close()
>>>>>>> a1142c0474d00fc43c6d8ed478a97b29eaa0bfed
