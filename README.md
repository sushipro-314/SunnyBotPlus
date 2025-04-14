# TunaCat
TunaCat is a open-source bot offering Moderation, Music, and more!
## BOT IS STILL IN DEVELOPMENT! If you want to help out or use the bot, know that a lot of features are unfinished or not implemented yet.
## Contributing
See [todo.md](https://github.com/sushipro-314/TunaCat/blob/master/todo.md) for a list of things that are being implemented
These may include primary features at the moment since the bot is still in development!
## Installation
Run the following commands to install the bot
```
git clone https://github.com/sushipro-314/TunaCat && 
cd ./TunaCat &&
python -m venv .venv &&
.\.venv\Scripts\activate.bat && 
pip install -r requirements.txt
```
Almost there! Now make a file that looks something like this, name it `config.json`, and fill out your **Token, Lavalink Information, Prefix, Database**, and server invite! (Prefix and server invite information are optional, leave as is to skip)
```
{
    "token": "DISCORD TOKEN GOES HERE!",
    "prefix": "tun!",
    "uris": {
        "database": "mongodb://localhost",
        "lavalink": [
            {
                "name": "default-node",
                "host": "localhost",
                "port": 80,
                "pass": "youshallnotpass",
                "region": "eu"
            }
        ]
    },
    "invite": "https://discord.gg/TCE7KWjc9R",
    "max_song_count": 15
}
```
## Starting the bot
Start the bot by running the command ``python main.py`` on windows. On linux do ``python3 main.py`` instead.
(NOTE: We do not support MacOS, and probably won't for a long time. you might be able to use brew or another packager for mac, but support isn't fully guaranteed)
