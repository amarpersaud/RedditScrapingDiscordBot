# RedditScrapingDiscordBot
Discord bot using Discord.py that scrapes a subreddit for keywords, then sends messages to a channel

## Installation
Rename files 'EXAMPLE.env' and 'EXAMPLEpraw.ini' by removing EXAMPLE from the name (giving '.env' and 'praw.ini'). These files do NOT contain any keys, tokens, IDs, or client secrets. You must fill them in with yours.
	
In '.env', add the following environment variables from your discord application (via devloper dashboard), and copy the channel and guild IDs:

```
TOKEN=
PUBLICKEY=
APPLICATIONID=
CHANNEL=
GUILDID=
```

Prepare praw.ini by filling in the following from the reddit application and the reddit account details. User Agent can be filled with some text such as PyBot.

```
client_id=
client_secret
password=
username=
user_agent=
```

Then, run the bot with 
```
python ./nbot.py
```

## Usage:
```
/kw-add [keywords] - Adds list of space delimited keywords
/kw-delete [keywords] - Deletes list of space delimited keywords
/kw-list - lists existing keywords
/kw-sub [keywords] - Subscribes to mentions to keywords
/kw-unsub [keywords] - Unsubscribes from mentions to keywords
/kw-unsub-all [keywords] - Unsubscribes from mentions to all keywords
/kw-subs - View those subscribed to a keyword
```

## Dependencies
- [discord.py](https://github.com/Rapptz/discord.py)
- praw
- asyncpraw
- python-dotenv
- asyncio
