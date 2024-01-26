import redis

redis_db=redis.Redis(host="localhost", port=6379, db=0)
redis_db.flushdb()


redis_db.hset("user1","total_score", 5) 
redis_db.hset("user1","game_count",1)
redis_db.hset("user2","total_score", 6)
redis_db.hset("user2","game_count",1)
redis_db.hset("user3","total_score", 4)
redis_db.hset("user3","game_count",1)
redis_db.hset("user4","total_score", 6)
redis_db.hset("user4","game_count",1)
redis_db.hset("user5","total_score", 0)
redis_db.hset("user5","game_count",1)
redis_db.hset("user6","total_score", 1)
redis_db.hset("user6","game_count",1)
redis_db.hset("user7","total_score", 3)
redis_db.hset("user7","game_count",1)
redis_db.hset("user8","total_score", 2)
redis_db.hset("user8","game_count",1)
redis_db.hset("user9","total_score", 5)
redis_db.hset("user9","game_count",1)
redis_db.hset("user10","total_score", 6)
redis_db.hset("user10","game_count",1)

redis_db.zadd("users", {"user1": 5})
redis_db.zadd("users", {"user2": 6})
redis_db.zadd("users", {"user3": 4})
redis_db.zadd("users", {"user4": 6})
redis_db.zadd("users", {"user5": 0})
redis_db.zadd("users", {"user6": 1})
redis_db.zadd("users", {"user7": 3})
redis_db.zadd("users", {"user8": 2})
redis_db.zadd("users", {"user9": 5})
redis_db.zadd("users", {"user10": 6})