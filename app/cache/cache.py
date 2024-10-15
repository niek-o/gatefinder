import redis

r = redis.Redis(host='cache', port=6379, db=0)


def add_to_cache(key, value):
    # Cache for 6 hours (60*60*6)
    r.set(key, value, ex=60*60*6)

    return


def get_from_cache(key):
    return r.get(key)
