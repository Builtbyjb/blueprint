import sqlite3
import redis

# Create a sqlite3 database engine
def sqlite():
    dbCon = sqlite3.connect("db.sqlite3")
    db = dbCon.cursor()
    db.execute("""
               CREATE TABLE IF NOT EXISTS user(id, refresh_token, access_token)
            """)
    return db, dbCon


def get_redis_client(redisURL):
    r = redis.Redis.from_url(redisURL,  decode_responses=True)
    return r
