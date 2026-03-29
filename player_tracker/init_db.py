from database import get_connection

conn = get_connection()
cur = conn.cursor()

# Players table
cur.execute("""
CREATE TABLE IF NOT EXISTS Players(
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
""")

# Matches table
cur.execute("""
CREATE TABLE IF NOT EXISTS Matches(
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    map TEXT
)
""")

# Stats table
cur.execute("""
CREATE TABLE IF NOT EXISTS Player_Match_Stats(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER,
    match_id INTEGER,
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    result TEXT,
    FOREIGN KEY(player_id) REFERENCES Players(player_id),
    FOREIGN KEY(match_id) REFERENCES Matches(match_id)
)
""")

conn.commit()
conn.close()

print("Database created successfully ✅")