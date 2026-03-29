
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from database import get_connection
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -------- BASIC APIs --------

@app.get("/players")
def get_players():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Players")
    rows = cur.fetchall()
    conn.close()

    return [{"player_id": r[0], "name": r[1]} for r in rows]


@app.get("/matches")
def get_matches():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Matches")
    rows = cur.fetchall()
    conn.close()

    return [{"match_id": r[0], "date": r[1], "map": r[2]} for r in rows]


@app.get("/stats")
def get_stats():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.name, m.match_id, ps.kills, ps.deaths, ps.assists, ps.result
    FROM Player_Match_Stats ps
    JOIN Players p ON ps.player_id = p.player_id
    JOIN Matches m ON ps.match_id = m.match_id
    """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "name": r[0],
            "match_id": r[1],
            "kills": r[2],
            "deaths": r[3],
            "assists": r[4],
            "result": r[5]
        }
        for r in rows
    ]


# -------- LEADERBOARD --------

@app.get("/leaderboard")
def leaderboard():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.name, SUM(ps.kills)
    FROM Players p
    JOIN Player_Match_Stats ps ON p.player_id = ps.player_id
    GROUP BY p.player_id
    ORDER BY SUM(ps.kills) DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return [{"name": r[0], "total_kills": r[1]} for r in rows]


@app.get("/winrate")
def winrate():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT 
        p.name,
        ROUND(
            SUM(CASE WHEN ps.result = 'win' THEN 1 ELSE 0 END) * 1.0 
            / COUNT(*), 2
        )
    FROM Players p
    JOIN Player_Match_Stats ps ON p.player_id = ps.player_id
    GROUP BY p.player_id
    ORDER BY 2 DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return [{"name": r[0], "win_rate": r[1]} for r in rows]


@app.get("/top_players")
def top_players():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.name, SUM(ps.kills)
    FROM Players p
    JOIN Player_Match_Stats ps ON p.player_id = ps.player_id
    GROUP BY p.player_id
    ORDER BY SUM(ps.kills) DESC
    LIMIT 3
    """)

    rows = cur.fetchall()
    conn.close()

    return [{"name": r[0], "kills": r[1]} for r in rows]


# -------- PLAYER GLOBAL --------

@app.get("/player/{player_id}")
def get_player(player_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT 
        p.name,
        COUNT(ps.match_id),
        SUM(ps.kills),
        SUM(ps.deaths),
        SUM(ps.assists),
        ROUND(SUM(ps.kills) * 1.0 / NULLIF(SUM(ps.deaths), 0), 2)
    FROM Players p
    JOIN Player_Match_Stats ps ON p.player_id = ps.player_id
    WHERE p.player_id = %s
    GROUP BY p.player_id
    """, (player_id,))

    r = cur.fetchone()
    conn.close()

    if not r:
        return {"error": "Player not found"}

    return {
        "name": r[0],
        "matches": r[1],
        "kills": r[2],
        "deaths": r[3],
        "assists": r[4],
        "kd_ratio": r[5]
    }


# -------- SEARCH / FILTER --------

@app.get("/search")
def search_player(name: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM Players WHERE name LIKE %s", ('%' + name + '%',))
    rows = cur.fetchall()
    conn.close()

    return [{"player_id": r[0], "name": r[1]} for r in rows]


@app.get("/stats_by_date")
def stats_by_date(date: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.name, ps.kills, ps.deaths, ps.assists
    FROM Player_Match_Stats ps
    JOIN Players p ON ps.player_id = p.player_id
    JOIN Matches m ON ps.match_id = m.match_id
    WHERE m.date = %s
    """, (date,))

    rows = cur.fetchall()
    conn.close()

    return [
        {"name": r[0], "kills": r[1], "deaths": r[2], "assists": r[3]}
        for r in rows
    ]


# -------- MATCH DETAILS --------

@app.get("/match/{match_id}")
def match_details(match_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.name, ps.kills, ps.deaths, ps.assists, ps.result
    FROM Player_Match_Stats ps
    JOIN Players p ON ps.player_id = p.player_id
    WHERE ps.match_id = %s
    """, (match_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "name": r[0],
            "kills": r[1],
            "deaths": r[2],
            "assists": r[3],
            "result": r[4]
        }
        for r in rows
    ]


# -------- TRACKER-STYLE APIs --------

@app.get("/player/{player_id}/overview")
def player_overview(player_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT 
        COUNT(match_id),
        SUM(kills),
        SUM(deaths),
        SUM(assists),
        ROUND(SUM(kills)*1.0/NULLIF(SUM(deaths),0),2),
        SUM(CASE WHEN result='win' THEN 1 ELSE 0 END)*1.0/NULLIF(COUNT(match_id), 0)
    FROM Player_Match_Stats
    WHERE player_id = %s
    """, (player_id,))

    r = cur.fetchone()
    conn.close()

    return {
        "matches": r[0] if r[0] is not None else 0,
        "kills": r[1] if r[1] is not None else 0,
        "deaths": r[2] if r[2] is not None else 0,
        "assists": r[3] if r[3] is not None else 0,
        "kd_ratio": r[4] if r[4] is not None else 0.0,
        "win_rate": round(r[5], 2) if r[5] is not None else 0.0
    }


@app.get("/player/{player_id}/matches")
def match_history(player_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT m.match_id, m.date, m.map,
           ps.kills, ps.deaths, ps.assists, ps.result
    FROM Player_Match_Stats ps
    JOIN Matches m ON ps.match_id = m.match_id
    WHERE ps.player_id = %s
    ORDER BY m.match_id DESC
    """, (player_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "match_id": r[0],
            "date": r[1],
            "map": r[2],
            "kills": r[3],
            "deaths": r[4],
            "assists": r[5],
            "result": r[6]
        }
        for r in rows
    ]


@app.get("/player/{player_id}/performance")
def performance(player_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT AVG(kills), AVG(deaths), AVG(assists)
    FROM Player_Match_Stats
    WHERE player_id = %s
    """, (player_id,))

    r = cur.fetchone()
    conn.close()

    return {
        "avg_kills": round(r[0], 2) if r[0] is not None else 0.0,
        "avg_deaths": round(r[1], 2) if r[1] is not None else 0.0,
        "avg_assists": round(r[2], 2) if r[2] is not None else 0.0
    }


@app.get("/player/{player_id}/maps")
def map_stats(player_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT m.map,
           COUNT(*),
           SUM(CASE WHEN ps.result='win' THEN 1 ELSE 0 END)*1.0/COUNT(*)
    FROM Player_Match_Stats ps
    JOIN Matches m ON ps.match_id = m.match_id
    WHERE ps.player_id = %s
    GROUP BY m.map
    """, (player_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {"map": r[0], "matches": r[1], "win_rate": round(r[2], 2)}
        for r in rows
    ]


@app.get("/player/{player_id}/weapons")
def weapon_stats(player_id: int):
    weapons = ["Vandal", "Phantom", "Operator"]

    return [
        {
            "weapon": w,
            "kills": random.randint(10, 100),
            "accuracy": random.randint(10, 80)
        }
        for w in weapons
    ]

# -------- CRUD APIs --------

from pydantic import BaseModel
from fastapi import HTTPException

class PlayerCreate(BaseModel):
    name: str

class PlayerUpdate(BaseModel):
    name: str

class MatchCreate(BaseModel):
    date: str
    map: str

class StatCreate(BaseModel):
    player_id: int
    match_id: int
    kills: int
    deaths: int
    assists: int
    result: str

@app.post("/players")
def create_player(player: PlayerCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Players (name) VALUES (%s)", (player.name,))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"message": "Player created", "player_id": new_id}

@app.put("/players/{player_id}")
def update_player(player_id: int, player: PlayerUpdate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Players SET name = %s WHERE player_id = %s", (player.name, player_id))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Player not found")
    conn.commit()
    conn.close()
    return {"message": "Player updated"}

@app.delete("/players/{player_id}")
def delete_player(player_id: int):
    conn = get_connection()
    cur = conn.cursor()
    # Delete stats associated with the player first (cascade)
    cur.execute("DELETE FROM Player_Match_Stats WHERE player_id = %s", (player_id,))
    cur.execute("DELETE FROM Players WHERE player_id = %s", (player_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Player not found")
    conn.commit()
    conn.close()
    return {"message": "Player deleted"}

@app.post("/matches")
def create_match(match: MatchCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Matches (date, map) VALUES (%s, %s)", (match.date, match.map))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"message": "Match created", "match_id": new_id}

@app.delete("/matches/{match_id}")
def delete_match(match_id: int):
    conn = get_connection()
    cur = conn.cursor()
    # Cascade delete stats
    cur.execute("DELETE FROM Player_Match_Stats WHERE match_id = %s", (match_id,))
    cur.execute("DELETE FROM Matches WHERE match_id = %s", (match_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Match not found")
    conn.commit()
    conn.close()
    return {"message": "Match deleted"}

@app.post("/stats")
def create_stat(stat: StatCreate):
    conn = get_connection()
    cur = conn.cursor()
    # Verify player and match exist
    cur.execute("SELECT * FROM Players WHERE player_id = %s", (stat.player_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Player not found")
        
    cur.execute("SELECT * FROM Matches WHERE match_id = %s", (stat.match_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Match not found")

    cur.execute("""
        INSERT INTO Player_Match_Stats (player_id, match_id, kills, deaths, assists, result) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (stat.player_id, stat.match_id, stat.kills, stat.deaths, stat.assists, stat.result))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"message": "Stat created", "stat_id": new_id}
