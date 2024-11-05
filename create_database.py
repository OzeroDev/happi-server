import sqlite3
con = sqlite3.connect("responses.db")
cur = con.cursor()

cur.execute('''DROP TABLE IF EXISTS responses''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt TEXT NOT NULL, 
        type TEXT NOT NULL,
        printedCount INT DEFAULT 0,
        verified INT DEFAULT 0
    )
''')

con.commit()