import sqlite3
import os

DB = 'movies.db'

if os.path.exists(DB):
    os.remove(DB)
    print(f"Removed existing {DB}")

conn = sqlite3.connect(DB)

with open('schema.sql') as f:
    conn.executescript(f.read())
print("Schema created.")

with open('seed.sql') as f:
    conn.executescript(f.read())
print("Seed data inserted.")

conn.commit()
conn.close()
print(f"Done. Database ready: {DB}")
