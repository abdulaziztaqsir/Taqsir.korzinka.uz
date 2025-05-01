import psycopg2

conn = psycopg2.connect("dbname=pdpschool user=postgres password=abdulaziztaqsir")


cur = conn.cursor()
# cur.execute("CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar(30));")
cur.execute("INSERT INTO test(num, data) values (20, 'va alaykum assalom');")

conn.commit()
cur.close()
conn.close()