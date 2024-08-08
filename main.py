import discord
from discord.ext import commands
from dotenv import load_dotenv
import random
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import requests
from name_mappings import name_mapping  
import os

load_dotenv()
TOKEN = os.environ['TOKEN']
YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

intents = discord.Intents.default()
intents.message_content = True  
bot = commands.Bot(command_prefix='!', intents=intents)

color_mapping = {
    'rare': 0x3498db,
    'epic': 0x9b59b6,
    'legendary': 0xf1c40f,  
    'mythical': 0xe74c3c,
    'mythic': 0xe74c3c
}

def get_channel_id(channel_name):
    try:
        request = youtube.search().list(
            part="snippet",
            q=channel_name,
            type="channel",
            maxResults=1
        )
        response = request.execute()
        items = response.get('items')
        if items:
            return items[0]['snippet']['channelId']
        else:
            return None
    except Exception as e:
        print(f"Error getting channel ID: {e}")
        return None

def get_random_video(channel_id):
    try:
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=1000,
            type="video",
            order="date"
        )
        response = request.execute()
        items = response.get('items')
        if items:
            video = random.choice(items)
            return f"https://www.youtube.com/watch?v={video['id']['videoId']}"
        else:
            return None
    except Exception as e:
        print(f"Error getting random video: {e}")
        return None

@bot.command(name='rv', aliases=['randomvideo', 'randomvid', 'rvid'])
async def random_video(ctx, *, channel_name: str = None):
    if channel_name is None:
        await ctx.send("Please provide a YouTube channel name. Usage: `!rv {youtube_channel}`")
        return
    
    channel_id = get_channel_id(channel_name)
    if channel_id:
        video_url = get_random_video(channel_id)
        if video_url:
            await ctx.send(f"Here's a random video from {channel_name}: {video_url}")
        else:
            await ctx.send("Couldn't find any videos for this channel.")
    else:
        await ctx.send("Couldn't find the channel. Please check the channel name and try again.")

def scrape_acd_info(name):
    formatted_name = name_mapping.get(name.lower(), name)
    url = f"https://acd.fandom.com/wiki/{formatted_name}"
    response = requests.get(url)

    if response.status_code != 200:
        return "Error: Unable to fetch the information.", None

    soup = BeautifulSoup(response.content, 'html.parser')
    content_div = soup.find('div', {'class': 'mw-parser-output'})


    # ABILITY INFORMATION
    ability_section = soup.find('div', {'class': 'mw-parser-output'})
    ability_info = "No ability information found."
    if ability_section:
        ability_text = ability_section.text
        start_index = ability_text.find("Ability Information")
        end_index = ability_text.find("Usage Guide")

        if start_index != -1 and end_index != -1:
            ability_info = ability_text[start_index + len("Ability Information"):end_index]
        
            lines = ability_info.strip().split('\n')
        
            for i, line in enumerate(lines):
                if ':' in line:
                    ability_name = line.split(':')[0]
                    description = line[len(ability_name)+1:].strip()
                    lines[i] = f"```{ability_name}:``` *{description}*"
        
            ability_info = '\n'.join(lines)
        
        else:
            print("Ability information section not found.")
    else:
        print("Ability section not found.")

    # RARITY
    rarity_element = soup.find('div', {'class': 'pi-data-value pi-font'})
    rarity = rarity_element.text.strip().lower() if rarity_element else 'rare'


    # CHARACTER PHRASE
    phrase = content_div.find('b')
    if phrase:
        phrase = phrase.text.strip()
        if phrase[0] == '"':
            phrase = phrase
        else: 
            phrase = None
    else:
        phrase = None



    # CHARACTER NAME
    charname = soup.find('span', {'class': 'mw-page-title-main'})
    charname_text = charname.text if charname else "Unknown Character"


    # CHARACTER IMAGE 
    image = soup.find('figure', {'class': 'pi-item pi-image'})
    if image:
        img_tag = image.find('img')
        if img_tag:
            src = img_tag.get('src')
            if src:
                image_url = src
                image_url = image_url.replace(" ", "")
            else:
                image_url = None
        else:
            image_url = None
    else:
        image_url = None


    if content_div:
        paragraph = content_div.find('p')
        text = paragraph.text if paragraph else "Error: No paragraph found."
        return text, image_url, charname_text, phrase, rarity, ability_info
    else:
        return "Error: Content not found.", None

@bot.command(name='acd', aliases=['animecrossoverdefense', 'anime crossover defense'])
async def acd(ctx, *, name: str):
    info, image_url, charname_text, phrase, rarity, ability_info = scrape_acd_info(name)

    color = color_mapping.get(rarity, 0xFFFFFF)

    embed = discord.Embed(title=charname_text,description=info,color=color)
    if image_url:
        embed.set_image(url=image_url)
    embed.set_footer(text="Anime Crossover Defense Web Scraper powered by Dionysus Bot.", icon_url="https://static.wikia.nocookie.net/fbtd/images/e/e6/Site-logo.png/revision/latest?cb=20240711144854")
    if phrase:
        embed.add_field(name="", value="*"+phrase+"*", inline=False)
    embed.add_field(name="``Ability Information``",value=ability_info,inline=True)


    await ctx.send(embed=embed)

@bot.command(name='commands', aliases=['cmds', 'cmd'])
async def commands(ctx):
    embed = discord.Embed(color=0x0d48a6)
    embed.set_author(name="Commands List",icon_url=ctx.guild.icon.url)
    embed.add_field(name="Anime Crossover Defense", value="`!acd {character_name}` - searches up information about the character in Anime Crossover Defense.", inline=False)
    embed.add_field(name="YouTube", value="`!rv {youtube_channel}` - RandomVideo or rv for short, chooses a random video from the chosen YouTube channel.", inline=False)
    embed.add_field(name="Tarot", value="`!tarot` - Draws a random tarot card and provides its meaning.", inline=False)
    embed.set_footer(text="Brought to you by Overjoy061", icon_url=ctx.bot.user.avatar.url)

    await ctx.send(embed=embed)


@bot.command()
async def tarot(ctx):
    tarot_meanings = {
        "The Fool": ("Upright: innocence, new beginnings, free spirit \nReversed: recklessness, taken advantage of, inconsideration", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-fool_350x500_crop_center.png?v=1488830339"),
        "The Magician": ("Upright: willpower, desire, creation, manifestation \nReversed: trickery, illusions, out of touch", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-magician_350x500_crop_center.png?v=1488831715"),
        "The High Priestess": ("Upright: intuitive, unconscious, inner voice \nReversed: lack of center, lost inner voice, repressed feelings", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-high-priestess_350x500_crop_center.png?v=1488835017"),
        "The Empress": ("Upright: motherhood, fertility, nature \nReversed: dependence, smothering, emptiness, nosiness", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-empress_350x500_crop_center.png?v=1488861619"),
        "The Emperor": ("Upright: authority, structure, control, fatherhood \nReversed: tyranny, rigidity, coldness", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-emperor_350x500_crop_center.png?v=1488863121"),
        "The Hierophant": ("Upright: tradition, conformity, morality, ethics \nReversed: rebellion, subversiveness, new approaches", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-hierophant_350x500_crop_center.png?v=1488864368"),
        "The Lovers": ("Upright: partnerships, duality, union \nReversed: loss of balance, one-sidedness, disharmony", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-lovers_350x500_crop_center.png?v=1488900062"),
        "The Chariot": ("Upright: direction, control, willpower \nReversed: lack of control, lack of direction, aggression", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-chariot_350x500_crop_center.png?v=1488905976"),
        "Strength": ("Upright: inner strength, bravery, compassion, focus \nReversed: self doubt, weakness, insecurity", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-strength_350x500_crop_center.png?v=1488907669"),
        "The Hermit": ("Upright: contemplation, search for truth, inner guidance \nReversed: loneliness, isolation, lost your way", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-hermit_350x500_crop_center.png?v=1488908379"),
        "The Wheel of Fortune": ("Upright: change, cycles, inevitable fate \nReversed: no control, clinging to control, bad luck", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-wheel-of-fortune_350x500_crop_center.png?v=1488919069"),
        "Justice": ("Upright: cause and effect, clarity, truth \nReversed: dishonesty, unaccountability, unfairness", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-justice_350x500_crop_center.png?v=1488920859"),
        "The Hanged Man": ("Upright: sacrifice, release, martyrdom \nReversed: stalling, needless sacrifice, fear of sacrifice", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-hanged-man_350x500_crop_center.png?v=1488921716"),
        "Death": ("Upright: end of cycle, beginnings, change, metamorphosis \nReversed: fear of change, holding on, stagnation, decay", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-death_350x500_crop_center.png?v=1488924469"),
        "Temperance": ("Upright: middle path, patience, finding meaning \nReversed: extremes, excess, lack of balance", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-temperance_350x500_crop_center.png?v=1489166942"),
        "The Devil": ("Upright: addiction, materialism, playfulness \nReversed: freedom, release, restoring control", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-devil_350x500_crop_center.png?v=1489167792"),
        "The Tower": ("Upright: sudden upheaval, broken pride, disaster \nReversed: disaster avoided, delayed disaster, fear of suffering", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-tower_350x500_crop_center.png?v=1489185889"),
        "The Star": ("Upright: hope, faith, rejuvenation \nReversed: faithlessness, discouragement, insecurity", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-star_350x500_crop_center.png?v=1489187135"),
        "The Moon": ("Upright: unconscious, illusions, intuition \nReversed: confusion, fear, misinterpretation", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-moon_350x500_crop_center.png?v=1489188353"),
        "The Sun": ("Upright: joy, success, celebration, positivity \nReversed: negativity, depression, sadness", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-sun_350x500_crop_center.png?v=1489190376"),
        "Judgement": ("Upright: reflection, reckoning, awakening \nReversed: lack of self awareness, doubt, self loathing", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-judgement_350x500_crop_center.png?v=1489191982"),
        "The World": ("Upright: fulfillment, harmony, completion \nReversed: incompletion, no closure", "https://labyrinthos.co/cdn/shop/articles/tarot-card-meanings-cheat-sheet-major-arcana-world_350x500_crop_center.png?v=1489193487")
    }
    tarot_card = random.choice(list(tarot_meanings.keys()))
    card_meaning, card_image_url = tarot_meanings[tarot_card]
    embed = discord.Embed(title=f"Your Tarot Card: {tarot_card}", description=card_meaning, color=0x00ff00)
    embed.set_image(url=card_image_url)
    await ctx.send(embed=embed)

bot.run(TOKEN)
