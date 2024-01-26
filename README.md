# Wordle Game API

## **Setting up Redis**
##### `sudo apt install --yes redis`
##### `sudo apt install --yes python3-hiredis`

## **Setting up NginxConfig**
#### Add Nginx config file "project4NginxConfig"  at path `/etc/nginx/sites-enabled`

## **Initializing SQLite and Redis Database & Start Service:**

##### `foreman start`
##### `./bin/init.sh`

##### Note: If you get error " ValueError: 'default' must be a list when 'multiple' is true". put "PYTHONNOUSERSITE=True rq worker --with-scheduler" in your procfile for worker process. 

## Retrying failed jobs
##### 1. Open cron editor using command crontab -e  
##### 2. Open cronfile from project director and Copy and paste content in cron edit and save. It will retry failed jobs every 10 mintues. 




## **Testing the APIs**
### Note: In order to run the API, you will ocasionally have to to supply specific variables. Any time this is required, please replace the < variable > with the correct information.

### **Game API**
#### `http://127.0.0.1:5100/docs`

#### Registers a new user.
#### `http POST http://games.local.gd/user/registration username=<USERNAME> userpassword=<PASSWORD>`

#### Game API get, will display the index page for game API.
#### `http --auth user:password http://games.local.gd/` 

#### Starts a new game for a player.
#### `http --auth user:password POST http://games.local.gd/newgame`

#### Allows the player to enter a 5 letter word to guess given a game ID.
#### Note: [Red : Incorrect Letter] [Yellow : Correct Letter, Incorrect Place] [Green : Correct Letter, Correct Place]
#### `http --auth user:password http://games.local.gd/guess game_id=<game_ID> guess_word=<guess>`

#### Prints all in progress games for the player.
#### `http --auth user:password http://games.local.gd/inprogressgame/`

#### Prints the status of a game given a game ID.
#### `http --auth user:password http://games.local.gd/gamestatus/<game_ID>`


### **Leaderboard Service**

#### API for retreiving top 10 users by average score
#### `http GET http://games.local.gd/top_10_user`



