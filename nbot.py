#!/usr/bin/python
from discord.ext import tasks, commands
from discord import app_commands
import discord
import asyncio

import asyncpraw
import time
import os
import logging
from threading import Thread
from dotenv import load_dotenv
import asyncio
import pickle
import atexit

from queue import Queue

keywordPath = './keywords.obj'
processedPath = './processed.obj'

class Expando(object):
    pass

client = None

load_dotenv()

disctoken = os.getenv('TOKEN')

helptext = ""
with open('./helptext.txt') as f:
    helptext = "\n".join(f.readlines())

def post_has_keyword(post, keyword):
    return (keyword.lower() in post.title.lower()) or (keyword.lower() in post.selftext.lower())

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.processedIDs = []
        self.keywords = []
        
        try:
            with open(keywordPath, 'rb') as f:
                self.keywords = pickle.load(f)
        except:
            print("Failed to open keywords file")
        
        try:
            with open(processedPath, 'rb') as f:
                self.processedIDs = pickle.load(f)
        except:
            print("Failed to open id file")
    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=discord.Object(os.getenv("GUILDID")))
        await self.tree.sync(guild=discord.Object(os.getenv("GUILDID")))
        self.my_background_task.start()
        
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
    
    @tasks.loop(seconds=30)  # task runs every 30 seconds
    async def my_background_task(self):
        print("Loop running")
        channel = None
        try:
            channel = self.get_channel(os.getenv('CHANNEL'))
            if(channel == None):
                channel = await self.fetch_channel(os.getenv('CHANNEL'))
        except Exception as e:
            print("Failed to get discord channel in background task")
            print(e)
            
        postcount = 5
        
        currentNewestPosts = []
        
        try:
            async with asyncpraw.Reddit('bot1') as reddit:
                subreddit = await reddit.subreddit("hardwareswap")
                async for p in subreddit.new(limit=postcount):
                    if(p.id not in self.processedIDs):
                        currentNewestPosts.append(p)
                        self.processedIDs.append(p.id)
                await reddit.close()
                    #remove processed ids
                while len(self.processedIDs) > (2 * postcount):
                    self.processedIDs.pop(0)
        except Exception as e:
            print("Failed to load reddit for some reason")
            print(e)
            
        print("Found "+ str(len(currentNewestPosts)) + " new posts")
        
        if(len(currentNewestPosts) != 0):
            for submission in currentNewestPosts:
                subbedusers = []
                subbedIDs = []
                keywordsFound = []
                
                for keyword in self.keywords:
                    if post_has_keyword(submission, keyword.text):
                        keywordsFound.append(keyword.text)
                        for su in keyword.subs:
                            if (su not in subbedIDs):
                                subbedIDs.append(su)
                                #Get the user, use fetch if get fails
                                usr = self.get_user(su)
                                if usr is None:
                                    usr = await self.fetch_user(su)
                                subbedusers.append(usr)
                if len(keywordsFound) > 0:
                    await channel.send("{}\nSubs: {}\nKeywords: {}".format(submission.url, ", ".join(map(lambda x: x.mention, subbedusers)), ", ".join(keywordsFound)))
                    print("Submitted link: {}\nContained {}".format(submission.title, ", ".join(keywordsFound)))
        try:
            with open(processedPath, "wb") as f:
                pickle.dump(self.processedIDs, f)
        except:
            print("Failed to save processed IDs")
            return

    
    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in
    

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
intents.guilds = True

client = MyClient(intents=intents)
@client.tree.command(name="kw-add")
async def addKeyword(interaction: discord.Interaction, keywords: str):
    """Adds keywords to list"""
    global client
    parts = keywords.split(' ')
    for pt in parts:
        if all(k.text != pt for k in client.keywords):
            keyword = Expando()
            keyword.text=pt
            keyword.subs=[]
            client.keywords.append(keyword);
    await interaction.response.send_message("Added keywords: " + (", ".join(parts)))
    with open(keywordPath, "wb") as f:
        pickle.dump(client.keywords, f)

@client.tree.command(name="kw-delete")
async def deleteKeyword(interaction: discord.Interaction, keywords: str):
    """Deletes keywords from list"""
    global client
    parts = keywords.split(' ')
    for pt in parts:
        for k in client.keywords:
            if(k.text == pt):
                client.keywords.remove(k)
    await interaction.response.send_message("Deleted keywords: " + (", ".join(parts)))
    with open(keywordPath, "wb") as f:
        pickle.dump(client.keywords, f)

@client.tree.command(name="kw-list")
async def listKeywords(interaction: discord.Interaction):
    """Lists keywords"""
    global client
    await interaction.response.send_message("Keywords: " + (", ".join(map(lambda x: x.text, client.keywords))))

@client.tree.command(name="kw-clear")
async def clearKeywords(interaction: discord.Interaction):
    """Lists keywords"""
    global client
    client.keywords=[]
    with open(keywordPath, "wb") as f:
        pickle.dump(client.keywords, f)
    await interaction.response.send_message("Cleared all keywords")
    
    
@client.tree.command(name="kw-help")
async def helpKeywords(interaction: discord.Interaction):
    """Lists keywords"""
    global helptext
    await interaction.response.send_message(helptext)
    
@client.tree.command(name="kw-sub")
async def subKeywords(interaction: discord.Interaction, keywords: str):
    """Subscribes user to keywords"""
    global client
    parts = keywords.split(' ')
    for pt in parts:
        keywordFound = False;
        #if keyword exists, add the user
        for kw in client.keywords:
            #keyword found
            if(kw.text == pt):
                keywordFound = True;
                #user is not already subbed
                if(interaction.user.id not in kw.subs):
                    kw.subs.append(interaction.user.id)
                break; #break out of for loop
        #if keyword wasnt found
        if(not keywordFound):
            #create new keyword, sub user
            kw = Expando()
            kw.subs = [interaction.user.id]
            kw.text = pt
            client.keywords.append(kw)
    with open(keywordPath, "wb") as f:
        pickle.dump(client.keywords, f)
    await interaction.response.send_message(interaction.user.name + " subbed to: " + (", ".join(parts)))


@client.tree.command(name="kw-subs")
async def showSubsKeywords(interaction: discord.Interaction, keywords: str):
    """Shows subs to keywords"""
    global client
    parts = keywords.split(' ')
    responsestring = "Users subscribed to keywords: \n"
    for pt in parts:    #for each fragment
        for keyword in client.keywords: #loop over and check if in keywords
            if(keyword.text == pt):     #if keyword found
                if(len(keyword.subs) == 0): #keyword has no subs
                    responsestring += "\"{}\": none\n\n".format(keyword.text);    
                else:
                    users = []    
                    for userid in keyword.subs:
                        usr = client.get_user(userid)
                        if usr is None:
                            usr = await client.fetch_user(userid)
                        users.append(usr)
                        
                    names = ", ".join(map(lambda x: x.name, users))
                    responsestring += "  \"{}\": {}\n\n".format(keyword.text, names);  
                break;
    await interaction.response.send_message(responsestring)

@client.tree.command(name="kw-unsub")
async def unsubKeywords(interaction: discord.Interaction, keywords: str):
    """Unsusbcribes from given keywords"""
    global client
    parts = keywords.split(' ')
    for pt in parts:
        for kw in client.keywords:
            if(kw.text == pt):
                if(interaction.user.id in kw.subs):
                    kw.subs.remove(interaction.user.id)
                break;
    await interaction.response.send_message(interaction.user.name + " unsusbscribed from keywords: " + (", ".join(parts)))

@client.tree.command(name="kw-unsub-all")
async def unsubKeywords(interaction: discord.Interaction, keywords: str):
    """Unsubscribes from all keywords"""
    global client
    parts = keywords.split(' ')
    for kw in client.keywords:
        if(interaction.user.id in kw.subs):
            kw.subs.remove(interaction.user.id)
    await interaction.response.send_message(interaction.user.name + " unsusbscribed from allkeywords")

client.run(disctoken)