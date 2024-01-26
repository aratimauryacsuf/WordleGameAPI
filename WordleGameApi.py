
from cmath import e
import collections
import dataclasses
import textwrap
import sqlite3
import databases
import toml
import random
import uuid
import itertools
import datetime
import requests
from my_module import send_score
from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import FailedJobRegistry

from quart import Quart, g, request, abort


from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

app = Quart(__name__)
QuartSchema(app)

app.config.from_file(f"./etc/{__name__}.toml", toml.load)
URL1 = app.config["DATABASES"]["PRIMARY_URL"]
URL2 = app.config["DATABASES"]["SECONDARY_1_URL"]
URL3 = app.config["DATABASES"]["SECONDARY_2_URL"]
url = itertools.cycle([URL1,URL2,URL3])



@dataclasses.dataclass
class guess:
    game_id: str
    guess_word: str


@dataclasses.dataclass
class client_url:
    url: str
    name: str

@dataclasses.dataclass
class completed:
    username: str
    guess_num: int
    outcome: str


async def _get_db_write():
    db = getattr(g, "_sqlite_db", None)
    db = g._sqlite_db = databases.Database(URL1)
    await db.connect()
    return db

async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    db = g._sqlite_db = databases.Database(next(url))
    await db.connect()
    return db


@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()


@app.route("/")
def index():
    return textwrap.dedent(
        """
        <h1>Welcome to the Game API</h1>

        """
    )

redis_conn = Redis()
q = Queue(connection=redis_conn)
registry = FailedJobRegistry(queue=q)

#All urls
#add parameter
async def enqueuejob(username, guess_num, outcome):
    db = await _get_db()
    sql = "SELECT client_url FROM Client_Urls"
    client_urls = await db.fetch_all(sql)
    for x in range(len(client_urls)):
        sampledict = {}
        sampledict["username"] = username
        sampledict["guess_num"] = guess_num
        sampledict["outcome"] = outcome
        sampledict["url"] = client_urls[0][x]
        result=q.enqueue(send_score, data = sampledict)

    return 0



    #get all urls
    #enqueue send_score

# Start of Game API



# Check if game_id present in db 
async def validate_game_id(game_id):
    db = await _get_db()
    sql = "SELECT game_id FROM Game WHERE game_id =:game_id "
    values = {"game_id": game_id}
    app.logger.info(sql)
    app.logger.info(values)
    game_id = await db.fetch_one(sql, values)
    if game_id is None:
        abort(404, "game  does not exist")
    else:
         return game_id

# function to update In_progress table
async def update_inprogress(username, game_id):
    db = await _get_db_write()
    inprogressEntry = await db.execute("INSERT INTO In_Progress(username, game_id) VALUES (:username, :game_id)", values={"username": username, "game_id": game_id})
    if inprogressEntry:
        return inprogressEntry
    else:
        abort(417, "Failed to create entry in In_Progress table")


# New Game API
@app.route("/newgame", methods=["POST"])
async def newgame():
    username = request.authorization.username
   
    db = await _get_db()

    sql = "SELECT correct_word FROM Correct_Words"
    app.logger.info(sql)
    secret_word = await db.fetch_all(sql)
    secret_word = random.choice(secret_word)
    username = username
    
    game = {}
    game["game_id"] = str(uuid.uuid4())
    game['username'] = str(username)
    game["secretword"] = str(secret_word[0])
    
    query = """INSERT INTO Game(game_id, username, secretword) 
        VALUES (:game_id, :username, :secretword)
        """
    db_write = await _get_db_write()
    result = await db_write.execute(query,game)
    if result:
        inprogressEntry = await update_inprogress(username, game["game_id"])
        game_id = game["game_id"]
        if inprogressEntry:
            return {"success": f"Your new game id is {game_id}"}, 201
        else:
            abort(417, "Failed to create entry in In_Progress table")

    else:
         abort(417, "New game creation failed")


@app.errorhandler(417)
def not_found(e):
    return {"error": str(e)}, 417


@app.errorhandler(404)
def not_found(e):
    return {"error": str(e)}, 404

    
#Guess API
@app.route("/guess", methods=["POST"])
@validate_request(guess)
async def guess(data):
    db = await _get_db() 
    
    payload = dataclasses.asdict(data) 
    game_id = await validate_game_id(payload["game_id"])
    
    sql= "SELECT username FROM Game WHERE game_id =:game_id "
    values={"game_id": game_id[0]}
    app.logger.info(sql)
    app.logger.info(values)
    username = await db.fetch_one(sql, values)
   
    guessObject = {}

    #Check if game is playable or complete. 
    sql = "SELECT * FROM In_Progress where game_id =:game_id "
    values={"game_id": game_id[0]}
    app.logger.info(sql)
    app.logger.info(values)
    in_progress = await db.fetch_all(sql,values)
    if not in_progress:
        return {"message": "Game has been completed already."}
    
    #Get secret word, format guess word, check if guess word is a valid word. 
    sql="SELECT secretword FROM Game where game_id =:game_id "
    values={"game_id": game_id[0]}
    app.logger.info(sql)
    app.logger.info(values)
   
    secret_word = await db.fetch_one(sql,values)
    secret_word = secret_word[0]
    guess_word = str(payload["guess_word"]).lower()

    sql_v = 'SELECT * FROM Valid_Words where valid_word =:valid_word'  
    values={"valid_word": guess_word}
    app.logger.info(sql_v)
    app.logger.info(values)
    is_valid_word_v = await db.fetch_all(sql_v,values)

    sql_c = 'SELECT * FROM Correct_Words where correct_word =:correct_word' 
    values={"correct_word": guess_word}
    app.logger.info(sql_c)
    app.logger.info(values)
    is_valid_word_c = await db.fetch_all(sql_c,values)
    if len(is_valid_word_v)==0 and len(is_valid_word_c)==0:
        return abort(404, "Not a Valid Word!")

    #Check guess count.
    sql = "SELECT Max(guess_num) FROM Guesses where game_id =:game_id" 
    values= {"game_id": game_id[0]}

    app.logger.info(sql)
    app.logger.info(values)
    guessEntry = await db.fetch_one(sql,values)
    guessCount = guessEntry[0]
    if guessCount == None:
        guessCount=0
    guessCount+=1
    guessObject["count"] = guessCount 

    #Check if guess is the secret word.
    sql = "SELECT guess_word FROM Guesses WHERE game_id =:game_id" 
    values= {"game_id": game_id[0]}
    app.logger.info(sql)
    app.logger.info(values)
    if guess_word==secret_word:
        db_write = await _get_db_write()

        guesses_word = await db.fetch_all(sql,values)
        loopCount=guessCount-1
        for i in range(loopCount):
            secret_wordcopy = secret_word     
            guess_wordloop = guesses_word[i][0]

            positionList = await guess_compute(guess_wordloop, secret_wordcopy, positionList=[])
            guessObject["guess"+str(i+1)] = positionList

        positionList = await guess_compute(guess_word, secret_word, positionList=[])
        guessObject["guess"+str(guessCount)] = positionList
        guessObject["message"]="You guessed the secret word!"
        insert_completed = await db_write.execute("INSERT INTO Completed(username, game_id, guess_num, outcome) VALUES(:username, :game_id, :guess_num, :outcome)", values={"username":username[0], "game_id":game_id[0], "guess_num":guessCount, "outcome":"Win"})
        await enqueuejob(username[0], guessCount, "Win")
        delete_inprogress = await db_write.execute("DELETE FROM In_Progress WHERE game_id=:game_id" ,values={"game_id":game_id[0]} )
        delete_guesses = await db_write.execute("DELETE FROM Guesses WHERE game_id=:game_id" ,values={"game_id":game_id[0]})
        return guessObject,200

    #Guess when the guess is not the secret word.  
    if guessCount<6:
        db_write = await _get_db_write()
        insert_guess = await db_write.execute("INSERT INTO Guesses(game_id, guess_num, guess_word) VALUES(:game_id, :guess_num, :guess_word)", values={"game_id": game_id[0], "guess_num": guessCount, "guess_word": guess_word})
        

        sql = "SELECT guess_word FROM Guesses WHERE game_id =:game_id" 
        values= {"game_id": game_id[0]}
        
        guesses_word = await db_write.fetch_all(sql,values)
        loopCount=guessCount-1
        for i in range(loopCount):
            secret_wordcopy = secret_word     
            guess_wordloop = guesses_word[i][0]

            positionList = await guess_compute(guess_wordloop, secret_wordcopy, positionList=[])
            guessObject["guess"+str(i+1)] = positionList

        positionList = await guess_compute(guess_word, secret_word, positionList=[])
        guessObject["guess"+str(guessCount)] = positionList
        guessObject["message"] = "Guess again!"
        return guessObject, 200

    #If this is 6th guess
    else:
        sql = "SELECT guess_word FROM Guesses WHERE game_id =:game_id" 
        values= {"game_id": game_id[0]}
        
        guesses_word = await db.fetch_all(sql,values)
        loopCount=guessCount-1
        for i in range(loopCount):
            secret_wordcopy = secret_word     
            guess_wordloop = guesses_word[i][0]

            positionList = await guess_compute(guess_wordloop, secret_wordcopy, positionList=[])
            guessObject["guess"+str(i+1)] = positionList

        positionList = await guess_compute(guess_word, secret_word, positionList=[])
        guessObject["guess"+str(guessCount)] = positionList
        
        guessObject["message"]="Out of guesses! Make a new game to play again. "

        db_write = await _get_db_write()

        complete_game = await db_write.execute("INSERT INTO Completed(username, game_id, guess_num, outcome) VALUES(:username, :game_id, :guess_num, :outcome)", values={"username": username[0], "game_id":game_id[0], "guess_num":guessCount, "outcome": "Lose"})
        await enqueuejob(username[0], guessCount, "Lose")
        delete_inprogress = await db_write.execute("DELETE FROM In_Progress WHERE game_id=:game_id" ,values={"game_id":game_id[0]})
        delete_guesses = await db_write.execute("DELETE FROM Guesses WHERE game_id=:game_id" ,values={"game_id":game_id[0]})
        return guessObject, 200
    


# Game Status API
@app.route("/gamestatus/<string:game_id>", methods=["GET"])
async def game_status(game_id):
    print(next(url))
    db = await _get_db()
    game_id = await validate_game_id(game_id)

    #Check if in completed:
    sql= "SELECT * FROM Completed WHERE game_id =:game_id" 
    values ={"game_id":game_id[0]}
    app.logger.info(sql)
    app.logger.info(values)
    game_id_completed = await db.fetch_one(sql,values)

    #If not completed:
    if game_id_completed == None:
        sql="SELECT secretword FROM Game WHERE game_id =:game_id" 
        values ={"game_id":game_id[0]}
        app.logger.info(sql)
        app.logger.info(values)
        secret_word1 = await db.fetch_one(sql,values)

        sql ="SELECT max(guess_num) FROM Guesses WHERE game_id =:game_id" 
        values ={"game_id":game_id[0]}
        app.logger.info(sql)
        app.logger.info(values)
        guesses_num = await db.fetch_all(sql,values)
        guessObject = {}
        if guesses_num[0][0] == None:
            guessObject["message"]="Game is currently in progress with no guesses."
            return guessObject, 200
        else:
            guessObject["message"]="Game is in progress with "+str(guesses_num[0][0])+" guesses."
            sql = "SELECT guess_word FROM Guesses WHERE game_id =:game_id" 
            values= {"game_id": game_id[0]}
            app.logger.info(sql)
            app.logger.info(values)
            guesses_word = await db.fetch_all(sql,values)
            for i in range(guesses_num[0][0]):
                loopNum=i+1
                secret_word = secret_word1[0]      
                guess_word = guesses_word[i][0]

                positionList = await guess_compute(guess_word, secret_word, positionList=[])
                guessObject["guess"+str(loopNum)] = positionList

    else:
        guessObject = {}
        if(game_id_completed[2]==6 and game_id_completed[3]=="Win"):
            guessObject["message"]="Game is completed and you have won with 6 guesses."
        elif (game_id_completed[2]==6 and game_id_completed[3]=="Lose"):
            guessObject["message"]="Game is completed and you have lost with 6 guesses."
        else:
            guessObject["message"]="Game is comleted and you have won with "+str(game_id_completed[2])+ " guesses."
    
    return guessObject, 200
        


# function to compute Guess API and Game status Logic
async def guess_compute(guess_word, secret_word,positionList):
    for j in guess_word:
        response = {}
        response[j] = "red"
        positionList.append(response)


    for i in range(5):
        if secret_word[i] in positionList[i].keys():
            positionList[i][list(positionList[i].keys())[0]] = "green"
            secret_word = secret_word[:i] + "_" + secret_word[i+1:]
                                

    for i,j in enumerate(guess_word):
        if j in secret_word and positionList[i][list(positionList[i].keys())[0]] != "green":
            positionList[i][list(positionList[i].keys())[0]] = "yellow"
            secret_word=secret_word.replace(j, "_")

    return positionList

# In progress game API
@app.route("/inprogressgame/", methods=["GET"])
async def get_inprogressgame():
    
    username = request.authorization.username
    
    db = await _get_db()
    sql = "SELECT game_id FROM In_Progress WHERE username = :username"
    values ={"username": username}
    app.logger.info(sql)
    app.logger.info(values)
    inprogressgames = await db.fetch_all(sql, values)
    if inprogressgames:
        inprogressgameObject={}
        
        if len(inprogressgames) >= 1:

            inprogressstring = str(inprogressgames[0][0])
            if len(inprogressgames) > 1:
                
                for i in range(len(inprogressgames)):
                    num = i+1
                    inprogressgameObject[f"game{num}"] =str(inprogressgames[i][0])
               
                return inprogressgameObject, 200
            return {"message": f"Your in progress game is {inprogressstring}"}, 200
    else:
       
        return {"message": f"There are no in progress games."}



#Register client URL API
@app.route("/register_url", methods=["POST"])
@validate_request(client_url)
async def register_url(data):
    #  print('testttttttt')
     client_url =dataclasses.asdict(data)
     print(client_url)
     db = await _get_db()
     sql="SELECT * FROM Client_Urls WHERE client_name = :client_name"
     values ={"client_name": client_url['name']}
     registered_client= await db.fetch_all(sql, values)
    #  print("registered_client************************")
    #  print(registered_client)
     
     db_write = await _get_db_write()
     print(client_url['url'])
     print(client_url['name'])
     try:
        
        if  not registered_client:
            query_result = await db_write.execute("INSERT INTO Client_Urls(client_name, client_url) VALUES(:client_name, :client_url)", values={"client_name":client_url['name'],"client_url": client_url['url']})
        else:
            # query= "update Client_Urls SET client_url= where client_name='leaderboard'"
            query_result = await db_write.execute("UPDATE  Client_Urls SET client_url =:client_url WHERE client_name =:client_name ", values={"client_name":client_url['name'],"client_url": client_url['url']})
     except sqlite3.IntegrityError as e:
        abort(409, e)
     if query_result:
        return {"success": "Client url registration successful"}, 201
     else:
        abort(417, "Client url registration failed")




