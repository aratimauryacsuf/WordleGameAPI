import textwrap
import dataclasses
import redis
import httpx
import os
import socket
from quart import Quart, abort, g, request
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request
import time



app = Quart(__name__)
QuartSchema(app)

#------- redis client object ---------#

redis_db=redis.Redis(host="localhost", port=6379, db=0)

@dataclasses.dataclass
class result:
    username: str
    game_status: str
    guess_count: int



def service_registration():
   
    success = False
    wait_time = 2
    while not success:
        try:
            hostname = socket.gethostbyname("localhost")
            env = os.environ
            port = env['PORT']
            leaderboard_url = f"http://{hostname}:{port}/report_result"
            game_service_url = 'http://game.local.gd/register_url'  
            response = httpx.post(game_service_url, json={'url': leaderboard_url, 'name':'leaderboard'})
            # if response.status_code != 201:
            #     continue
            success = True
            print("client registration successful") 
        except Exception as e:
            print(f"service registration failed retrying after{wait_time}")
            time.sleep(wait_time)
            wait_time += 2 
            continue


service_registration()



@app.route("/")

def index():
    return textwrap.dedent(
        """
        <h1>Welcome to the Leaderboard API</h1>
        """
    )


@app.route("/report_result", methods=["POST"])
@validate_request(result)
def report_result(data):
    result =dataclasses.asdict(data)

#---------------------computing score based on game result------------------------#

    if(result["game_status"].lower()== 'win') and (result["guess_count"]== 6):
        score =1
    elif (result["game_status"].lower()== 'win') and (result["guess_count"]== 5):
        score = 2
    elif (result["game_status"].lower()== 'win') and (result["guess_count"]== 4):
        score=3
    elif (result["game_status"].lower()== 'win') and (result["guess_count"]== 3):
        score = 4
    elif (result["game_status"].lower()== 'win') and (result["guess_count"]== 2):
        score= 5
    elif (result["game_status"].lower()== 'win') and (result["guess_count"]== 1):
        score = 6
    elif (result["game_status"].lower()== 'loss') and (result["guess_count"]== 6):
        score = 0
    else:
        return "Please enter game status win or loss and guess count between 1 to 6" , 403

#-------------------- end of computing score based on game result------------------------#


#-----------Using hash datatype --------------# 
    

    count =1
    if not (redis_db.hexists(result["username"],"total_score")):
        redis_db.hset(result["username"],"total_score", score)
        redis_db.hset(result["username"],"game_count",count)
    else:  
        redis_db.hincrby(result["username"],"total_score",score)
        redis_db.hincrby(result["username"],"game_count",count)

    
    total_score = int(redis_db.hget(result["username"],"total_score"))
    total_game =int(redis_db.hget(result["username"],"game_count"))

    avg_score = total_score /total_game
    

 #-----------End of Using hash datatype --------------# 


#--------Adding the computed result to sorted set---------#

    redis_db.zadd("users", {result["username"]: avg_score})
    
#--------End of adding the computed result to sorted set---------#
    
    return {"message": " Result posted successfully"},200


@app.route("/top_10_user", methods=["GET"])
def _get_top10_user():
    
    top10_user = redis_db.zrevrange("users",0,9,withscores=True)
   
    top10_user_object =[]
    
    for user in top10_user:
        user_object={}
        user_object[str(user[0],'UTF-8')] = float(user[1])
        top10_user_object.append(user_object)


    return top10_user_object, 200
