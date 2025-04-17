import redis

def get_redis_client(redisURL):
    r = redis.Redis.from_url(redisURL,  decode_responses=True)
    return r
