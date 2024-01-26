user: hypercorn UsersApi --reload --debug --bind UsersApi.local.gd:$PORT --access-logfile - --error-logfile - --log-level DEBUG
game_primary: ./bin/litefs --config ./etc/game_primary.yml
game_secondary_1: ./bin/litefs --config ./etc/game_secondary_1.yml
game_secondary_2: ./bin/litefs --config ./etc/game_secondary_2.yml
leaderboard: hypercorn leaderboardApi --reload --debug --bind leaderboardApi.local.gd:$PORT --access-logfile - --error-logfile - --log-level DEBUG
worker: rq worker --with-scheduler
