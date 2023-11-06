import requests
from lxml import html
import sqlite3
import os
import re

# Script version
SCRIPT_VERSION = "1.2"
SCRIPT_URL = "https://raw.githubusercontent.com/origamiofficial/samftp-rclone-updater/main/main.py"

# Telegram information
TELEGRAM_CHAT_ID = "XXXXXXXXXXXXXX"
TELEGRAM_BOT_API_KEY = "XXXXXXXXXX:XXX-XXXXXXXXXXXXXXXXXXXX_XXXXXXXXXX"

# URL and XPath information for SamFTP page
WEBSITE_URL = "http://172.16.50.5/"
LINK_XPATH = "//li/a[@class='hvr-bounce-to-bottom']/@href"
HYPERTEXT_XPATH = "//li/a[@class='hvr-bounce-to-bottom']/text()"

# Rclone configuration file
RCLONE_CONF_FILE = "/home/user/.config/rclone/rclone.conf"

# SQLite database information
DB_NAME = "samftp_links.db"
DB_TABLE_NAME = "links"

# Mapping of HTML names to RCLONE.CONF names
name_mappings = {
    "Animation Movies -1080p": "AnimationMovie1080",
    "Animation Movies": "AnimationMovie",
    "Cartoon TV Series": "AnimationSeries",
    "KOREAN TV & WEB Series": "KoreanSeries",
    "Foreign Language Movies": "ForeignLanguageMovies",
    "South-Movie Hindi Dubbed": "Sindian",
    "Hindi Movies": "Hindi",
    "English Movies -1080p ": "English1080",
    "English Movies": "English",
}

def is_website_up(url):
    print("Checking if SamFTP website is up...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("SamFTP website is up.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error: Unable to access the website ({url}): {e}")
        return False

def check_valid_xpaths(tree, xpaths):
    invalid_xpaths = []
    for xpath_name, xpath in xpaths.items():
        elements = tree.xpath(xpath)
        if len(elements) == 0:
            invalid_xpaths.append((xpath_name, xpath))
    return invalid_xpaths

def fetch_posts_data(url, link_xpath, hypertext_xpath):
    try:
        page = requests.get(url)
        page.raise_for_status()
        tree = html.fromstring(page.content)
        links = tree.xpath(link_xpath)
        hypertexts = tree.xpath(hypertext_xpath)
        return list(zip(hypertexts, links))
    except requests.exceptions.RequestException as e:
        print(f"Error fetching posts data: {e}")
        return []

def send_telegram_notification(chat_id, bot_api_key, message):
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_api_key}/sendMessage?chat_id={chat_id}&text={message}")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram notification: {e}")

def check_rclone_conf_up_to_date(rclone_conf_lines, database, name_mappings):
    rclone_conf_updated = False  # Flag to check if rclone.conf has been updated

    for hypertext, rclone_name in name_mappings.items():
        c.execute("SELECT link FROM {} WHERE hypertext=?".format(DB_TABLE_NAME), (hypertext,))
        result = c.fetchone()
        if result:
            new_url = result[0]
            # Initialize a flag to determine whether to update the "url" value
            update_url = False
            for i, line in enumerate(rclone_conf_lines):
                if re.search(f"\[{rclone_name}\]", line):
                    # When a section is found, set the flag to update the "url" value
                    update_url = True
                elif update_url and line.startswith("url"):
                    # Update the "url" value if the flag is set
                    if not line.strip().endswith(new_url):
                        # Check if the URL is different
                        rclone_conf_lines[i] = f"url = {new_url}\n"
                        print(f"URL for {hypertext} updated in rclone.conf.")
                        rclone_conf_updated = True  # Set the flag to indicate an update
                    # Reset the flag after checking or updating
                    update_url = False
        else:
            print(f"No URL found in the database for {hypertext}. Skipping update.")

    if rclone_conf_updated:
        return rclone_conf_lines
    else:
        return None  # Return None if no updates were made

# Check if SamFTP website is up
if not is_website_up(WEBSITE_URL):
    exit()

# Check XPath expressions
try:
    page = requests.get(WEBSITE_URL)
    page.raise_for_status()
    tree = html.fromstring(page.content)
    xpaths = {
        "LINK_XPATH": LINK_XPATH,
        "HYPERTEXT_XPATH": HYPERTEXT_XPATH
    }
    invalid_xpaths = check_valid_xpaths(tree, xpaths)
    if invalid_xpaths:
        print("Error: Invalid XPath expressions found:")
        for xpath_name, xpath in invalid_xpaths:
            print(f"{xpath_name}: No elements found for {xpath}")
        print("XPath expressions may need to be updated. Exiting script.")
        exit()
    num_items_found = len(tree.xpath(HYPERTEXT_XPATH))
    print(f"All XPath expressions are valid and found {num_items_found} items.")
except requests.exceptions.RequestException as e:
    print(f"Error checking XPath expressions: {e}. XPath expressions may need to be updated. Exiting script.")
    exit()

# Check if database file exists
if os.path.exists(DB_NAME):
    print("Existing SQLite database file found.")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM {}".format(DB_TABLE_NAME))
    num_items_in_db = c.fetchone()[0]
    print(f"{num_items_in_db} items found in the database.")
else:
    print("Existing SQLite database file not found, created one")

# Connect to SQLite database
print("Connecting to SQLite database...")
try:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    print("Connection to database successful.")
except sqlite3.Error as e:
    print(f"Error connecting to the database: {e}")
    exit()

# Check if links table exists in the database, and create it if it doesn't
try:
    c.execute(
        "CREATE TABLE IF NOT EXISTS {} (hypertext text, link text)".format(
            DB_TABLE_NAME
        )
    )
except sqlite3.Error as e:
    print(f"Error creating table: {e}")
    exit()

# Read rclone.conf file
try:
    with open(RCLONE_CONF_FILE, "r") as f:
        rclone_conf_lines = f.readlines()
except FileNotFoundError as e:
    print(f"Error reading rclone.conf file: {e}")
    exit()

# Fetch previously updated hypertexts from the database
previously_updated_hypertexts = set()
c.execute("SELECT hypertext FROM {}".format(DB_TABLE_NAME))
for row in c.fetchall():
    previously_updated_hypertexts.add(row[0])

# Fetch post data from the website
website_posts = fetch_posts_data(WEBSITE_URL, LINK_XPATH, HYPERTEXT_XPATH)

# Create a set to keep track of items that have been updated or added
updated_items = set()

# Iterate through website posts and update the database
database_updated = False # Flag to check if database has been updated
for hypertext, link in website_posts:
    if hypertext in previously_updated_hypertexts:
        # The item has been previously updated, check if the link is different
        c.execute("SELECT link FROM {} WHERE hypertext=?".format(DB_TABLE_NAME), (hypertext,))
        existing_link = c.fetchone()[0]
        if existing_link != link:
            # Link has been edited, update it in the database
            c.execute("UPDATE {} SET link=? WHERE hypertext=?".format(DB_TABLE_NAME), (link, hypertext))
            conn.commit()
            print(f"Link for {hypertext} has been updated in the database.")
            updated_items.add(hypertext)  # Add to the set of updated items
            database_updated = True  # Set the flag to indicate a database update
    else:
        # New post, add it to the database
        c.execute("INSERT INTO {} VALUES (?, ?)".format(DB_TABLE_NAME), (hypertext, link))
        conn.commit()
        print(f"New post for {hypertext} has been added to the database.")
        previously_updated_hypertexts.add(hypertext)
        updated_items.add(hypertext)  # Add to the set of updated items
        database_updated = True  # Set the flag to indicate a database update

# Check if the database is up-to-date or updated
if database_updated:
    print("Database has been updated.")
else:
    print("Database is up-to-date.")

# Update the "url" values in the rclone.conf file from the database
updated_rclone_conf = check_rclone_conf_up_to_date(rclone_conf_lines, c, name_mappings)

if updated_rclone_conf:
    # If updates were made, write the updated rclone.conf file
    try:
        with open(RCLONE_CONF_FILE, "w") as f:
            f.writelines(updated_rclone_conf)
        print("rclone.conf file updated.")
    except IOError as e:
        print(f"Error writing updated rclone.conf file: {e}")
else:
    print("Rclone config is up-to-date.")

# Send notification via Telegram for each updated post
for hypertext in updated_items:
    message = f"Attention, SamFTP's {hypertext} has been updated."
    send_telegram_notification(TELEGRAM_CHAT_ID, TELEGRAM_BOT_API_KEY, message)
    print(f"Notification sent via Telegram for {hypertext}.")

# Close connection to the database
conn.close()
print("Connection to the database closed.")
print("Script completed.")
