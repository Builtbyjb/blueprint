import sqlite3

# Create a sqlite3 database engine
def sqlite():
    dbCon = sqlite3.connect("db.sqlite3")
    db = dbCon.cursor()
    db.execute("""
               CREATE TABLE IF NOT EXISTS tasks (id, user_id, task, is_completed)
            """)
    return db, dbCon
