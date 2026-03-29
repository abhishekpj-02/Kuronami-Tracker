from database import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("SELECT * FROM Players")
print("Players:", cur.fetchall())

cur.execute("SELECT * FROM Matches")
print("Matches:", cur.fetchall())

cur.execute("SELECT * FROM Player_Match_Stats LIMIT 5")
print("Stats sample:", cur.fetchall())

conn.close()