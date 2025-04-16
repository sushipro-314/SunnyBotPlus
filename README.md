# TunaCat
TunaCat is a open-source bot offering Moderation, Music, and more!
## BOT IS STILL IN DEVELOPMENT! If you want to help out or use the bot, know that a lot of features are unfinished or not implemented yet.
## Contributing
See [todo.md](https://github.com/sushipro-314/TunaCat/blob/master/todo.md) for a list of things that are being implemented

These may include primary features at the moment since the bot is still in development!
## Installation
### Pre-requisites
- Python
- FFMPEG
- LavaLink Nodes. [Public Nodes can be found here](https://lavalink.darrennathanael.com/)
- A MongoDB Database
## Instructions
Run the following commands to install the bot
```
git clone https://github.com/sushipro-314/TunaCat && 
cd ./TunaCat &&
pip install -r requirements.txt
```
Almost there! Now make a file that looks something like this, name it `config.json`, and fill out your **Token, Lavalink Information, Prefix, Database, shard IDs**, and server invite! (Prefix and server invite information are optional, leave as is to skip)
```
{
    "token": "",
    "prefix": "tun!",
    "uris": {
        "database": "mongodb://localhost",
        "lavalink": [
            {
                "name": "main",
                "host": "localhost",
                "port": 2333,
                "pass": "youshallnotpass12324"
            },
        ]
    },
    "invite": "https://discord.gg/TCE7KWjc9R",
    "max_song_count": 15,
    "shard_ids": [
        0
    ]
}
```
## Starting the bot
Start the bot by running the command ``python main.py`` on windows. On linux do ``python3 main.py`` instead.

NOTES: 
- NOTE: **Add a folder called "logs" in the root directory if you are having issues starting the bot**
- NOTE: We do not support MacOS, and probably won't for a long time. you might be able to use brew or another packager for mac, but support isn't fully guaranteed
