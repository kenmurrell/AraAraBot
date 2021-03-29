# AraAraBot
 
An anime-themed discord bot for my buddy trident91

## Setup
To setup the bot, run the following in bash (Git Bash on Win10)

1) Setup ffmpeg and directories automatically:
```shell
$ bash setup.sh
```

2) Install python requirements:
```shell
$ pip3 install -r requirements.txt
```

3) Register the Discord bot on your server and add the access key to the `config.yaml` file. 
   

4) Run program:
```shell
$ python3 bot.py
```


## Commands
* `!join`: join the voice channel the user is currently in.
* `!leave`: leave the voice channel the bot is currently in.
* `!play [youtube link]`: play a youtube link or start playing the queue.
  * _NOTE: not configured to handle youtube playlists yet._
* `!queue [youtube link]`: queue up a youtube link to play.
* `!clearqueue`: clear the queue.
* `!pause`: pause/unpause the currently playing music.
* `!uptime`: show the current uptime of the bot.
* `!skip`: vote to skip the current track

