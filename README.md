# AraAraBot
 
An anime-themed discord bot for my buddy trident91

## Setup
To setup the bot, run the following in bash (Git Bash on Win10)

1) To download the **ffmpeg** drivers, create the directories and download the python requirements, run the following in bash:
```shell
$ bash setup.sh
```
_Note: this setup only works on Windows; for Linux/Mac you will need to install ffmpeg yourself_

2) Register the Discord bot on your server and add the access key to the `config.yaml` file. 

4) Run program:
```shell
$ python3 bot.py
```


## Commands
* `!join`: join the voice channel the user is currently in.
* `!leave`: leave the voice channel the bot is currently in.
* `!play [youtube link]`: play a youtube link or start playing the queue.
* `!queue [youtube link]`: queue up a youtube link to play.
* `!list`: show the songs currently in the queue.
* `!clear`: clear the queue.
* `!pause`: pause/unpause the currently playing music.
* `!uptime`: show the current uptime of the bot.
* `!skip`: vote to skip the current track
* `!kill`: kill the bot

