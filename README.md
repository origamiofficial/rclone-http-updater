# Rclone Http Backend URL Updater

A Python script that updates rclone configuration file (rclone.conf) with the latest URLs from specified website using XPath, and notifies via Telegram if changes are detected.

## Features

- Automatically checks if the website is up and running.
- Verifies the correctness of XPath expressions used to extract data from the website.
- Stores information about the website links in an SQLite database to track updates.
- Updates the rclone configuration file (rclone.conf) with the latest URLs from the website.
- Notifies specified Telegram channel about updates using the Telegram Bot API.

## Requirements

- Python 3.6 or higher
- `requests` library
- `lxml` library
- `sqlite3` library
- `TELEGRAM_CHAT_ID` and `TELEGRAM_BOT_API_KEY` environment variables with valid values

## Usage

1. Clone or download this repository.
2. Install the required libraries by running the following command:

```bash
pip install -r requirements.txt
```
3. Set the `WEBSITE_URL` environment variable with the website you want to fetch.
4. Set the `TELEGRAM_CHAT_ID` and `TELEGRAM_BOT_API_KEY` environment variables with your Telegram chat ID and bot API key.
5. Change the `name_mappings` according to your setup
```
"Website Hypertext": "Rclone Remote Name",
```

6. Run the script using the following command:

```bash
python main.py
```

## Contribution

If the website administrators make changes and break things, you may need to update the XPath expressions. Contributions in the form of pull requests are welcome. Remember that you don't need to update the script version if you make changes; the script will automatically update itself.

## How it works

The Rclone Http Backend URL Updater script is written in Python and uses various libraries to perform its tasks. It utilizes the requests library to fetch the website, and the lxml library to parse the HTML on the page and extract relevant information using specified XPath values. The script connects to an SQLite database to check if a link is already in the database. If yes, it compares the old link with the new link and updates the link in the database, then updates the rclone configuration file (rclone.conf) with the new URL. It sends notifications to a Telegram channel using the [Telegram Bot API](https://core.telegram.org/bots/api) with the information about the updated URL. The script uses the TELEGRAM_CHAT_ID and TELEGRAM_BOT_API_KEY environment variables to send notifications to the Telegram chat.

## Credit

Everything in this repo developed using natural language processing capabilities from OpenAI's GPT-3.5

[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https://github.com/origamiofficial/rclone-http-updater&icon=github.svg&icon_color=%23FFFFFF&title=hits&edge_flat=false)](https://github.com/origamiofficial/rclone-http-updater)
