import redis

def get_redis_client(redisURL): return redis.Redis.from_url(redisURL,  decode_responses=True)
