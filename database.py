import psycopg2

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

