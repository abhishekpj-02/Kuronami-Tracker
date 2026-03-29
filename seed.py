import random
from database import get_connection

conn = get_connection()
cur = conn.cursor()

# 🎮 Sample player names
players = ["Rayid", "Karthik", "Elias", "Abhishek", "Jett", "Viper", "Phoenix"]

# Insert players
for p in players:
    cur.execute("INSERT INTO Players(name) VALUES(?)", (p,))

# Insert matches
for i in range(5):
    cur.execute("INSERT INTO Matches(date, map) VALUES(?, ?)", ("2026-03-26", "Ascent"))

# Insert stats
for player_id in range(1, 8):
    for match_id in range(1, 6):
        cur.execute("""
        INSERT INTO Player_Match_Stats(player_id, match_id, kills, deaths, assists, result)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            player_id,
            match_id,
            random.randint(5, 30),
            random.randint(1, 20),
            random.randint(0, 10),
            random.choice(["win", "loss"])
        ))

conn.commit()
conn.close()

print("Data inserted successfully 🔥")