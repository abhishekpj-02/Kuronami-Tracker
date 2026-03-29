from init_db import *
from database import get_connection

# Only seed if Players table is empty
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM Players")
count = cur.fetchone()[0]
conn.close()

if count == 0:
    print("Seeding database...")
    from seed import *
else:
    print(f"Database already has {count} players, skipping seed.")