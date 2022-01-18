import io  # For ColorThief raw file
import json
from datetime import datetime  # For time

import psycopg2  # Heroku Database
import requests  # Download image link
from discord_webhook import DiscordEmbed, DiscordWebhook  # connnect to discord
from environs import Env  # For environment variables
import requests  # Download image link
from colorthief import ColorThief  # Find the dominant color
from selenium import webdriver  # Browser prereq

# Setting up environment variables
env = Env()
env.read_env()  # read .env file, if it exists

# connnecting with the heroku database
DATABASE_URL = env('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL, sslmode='require')

#  create a new cursor
cur = conn.cursor()


def embed_to_discord(date, image_url, caption):
    # Webhooks to send to
    webhook = DiscordWebhook(url=env.list("WEBHOOKS"))

    # create embed object for webhook
    embed = DiscordEmbed(title="The New Yorker",
                         color=dominant_image_color(image_url))

    # Captioning the image
    embed.add_embed_field(name="‎", value=caption, inline=False)

    embed.set_author(name=date)

    embed.set_image(url=image_url)

    # set thumbnail
    embed.set_thumbnail(
        url='https://www.clipartkey.com/mpngs/m/270-2705257_man-new-yorker-logo.png')

    # set footer
    embed.set_footer(text='Ibrahim Mudassar')

    # set timestamp (needs unix int)
    embed.set_timestamp()

    # add embed object to webhook(s)
    webhook.add_embed(embed)
    webhook.execute()


def restful_send(notification):
    body = json.dumps({

        "notification": notification,

        "accessCode": env("ACCESS_CODE")

    })

    requests.post(url="https://api.notifymyecho.com/v1/NotifyMe", data=body)

# Takes the image link, downloads it, and then returns a hex color code of the most dominant color


def dominant_image_color(image_link):
    r = requests.get(image_link, allow_redirects=True)

    color_thief = ColorThief(io.BytesIO(r.content))
    dominant_color = color_thief.get_color(quality=3)
    hex = '%02x%02x%02x' % dominant_color
    return hex


def last_entry():
    cur.execute("SELECT data FROM records")
    answer = cur.fetchone()
    if answer is None:
        return None
    else:
        return ''.join(answer)


# Create new Instance of Chrome
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = env("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")

browser = webdriver.Chrome(executable_path=env(
    'CHROMEDRIVER_PATH'), options=chrome_options)
browser.get("https://www.newyorker.com/magazine")


date = browser.find_element_by_xpath(
    "/html/body/div[2]/div/main/section/div[2]/header/div/h2").text
image = browser.find_element_by_xpath(
    "/html/body/div[2]/div/main/section/div[2]/header/div/div[1]/div/div/a/figure/div/div[2]/div/picture/img").get_attribute("src")
caption = browser.find_element_by_xpath(
    "/html/body/div[2]/div/main/section/div[2]/header/div/div[1]/div/div/a/figure/figcaption/span/p").text

if last_entry() != date or last_entry() == None:

    embed_to_discord(date=date, image_url=image, caption=caption)
    cur.execute(f"INSERT INTO records (data) VALUES ('{date}')")


conn.commit()
conn.close()

browser.quit()
