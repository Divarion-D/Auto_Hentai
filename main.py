# sourcery skip: avoid-builtin-shadow
from pyrogram import Client
from pyrogram.types import *
import os
import requests
import subprocess
from pymongo import MongoClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram.types import InputMediaPhoto, InputMediaVideo

API_ID = os.environ.get("API_ID", None) 
MONGO_URL = os.environ.get("MONGO_URL", None) 
API_HASH = os.environ.get("API_HASH", None) 
BOT_TOKEN = os.environ.get("BOT_TOKEN", None) 
CHANNEL_ID = os.environ.get(int("CHANNEL_ID"))
CHANNEL_URL = os.environ.get("CHANNEL_URL", None) 

app = Client(
    "hentai",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

hentaidb = MongoClient(MONGO_URL)

async def autohentai_parser():  # sourcery skip: avoid-builtin-shadow 
    db = hentaidb["HentaiDb"]["Name"]
    url = "https://hanime.metavoid.info/recent"
    result = requests.get(url)
    result = result.json()

    hent_id = result["reposone"][0]["id"]
    slug = result["reposone"][0]["slug"]
    name = result["reposone"][0]["name"]
    cover = requests.get(result["reposone"][0]["cover_url"])
    poster = requests.get(result["reposone"][0]["poster_url"])
    tags = result["reposone"][0]["tags"]
    # split the array with a comma and add a # at the beginning of each word and replace spaces and dashes with underscores
    tags = ", ".join(["#" + tag.replace(" ", "_").replace("-", "_") for tag in tags])

    is_hentai = db.find_one({"slug": slug})
    if not is_hentai:
        l = f"https://hanime.metavoid.info/link?id={slug}"
        k = requests.get(l)
        if k.status_code == 200:
            data = k.json()

            open('poster.jpg', 'wb').write(poster.content)
            open('cover.jpg', 'wb').write(cover.content)

            poster = 'poster.jpg'
            cover = 'cover.jpg'

            for i in data["data"]:
                file_url = i["url"]
                if i["height"] == "480":
                    break
            file = f'{slug}-480p.mp4'

            subprocess.run(
                f"ffmpeg -i {file_url} -acodec copy -vcodec copy -y {file}", shell=True)

            caption = f"""<a href="{CHANNEL_URL}">{name}</a>\n\n"""
            caption += f"""<b>Tags:</b> #id{hent_id} ,{tags}\n\n"""

            await app.send_media_group(
                CHANNEL_ID,
                [
                    InputMediaPhoto(cover),
                    InputMediaVideo(file, thumb=f'{poster}', caption=caption, parse_mode="html")
                ]
            )
            db.insert_one({"slug": slug})

            os.remove(file)

            os.remove(poster)
            os.remove(cover)


scheduler = AsyncIOScheduler()
scheduler.add_job(autohentai_parser, "interval", minutes=1, max_instances=1)
scheduler.start()

app.run()



