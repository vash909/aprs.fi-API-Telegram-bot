Features


- Fetch APRS data (position and weather) for a given callsign using the aprs.fi API.

- Set or change the callsign from within Telegram (no code modifications needed).

- Configure the update interval in seconds from within the Telegram chat.

- Start and Stop the bot via commands.

- Each chat can have its own unique callsign and unique interval.
  

Requirements

- Python 3.6+ (The bot is written for Python 3 and uses python-telegram-bot).

- requests library for HTTP requests.

- APScheduler for scheduling periodic tasks.
  
- A valid Telegram Bot Token (obtainable via BotFather on Telegram).
  
- A valid APRS.fi API key (obtainable via aprs.fi account settings).



Install dependencies:

pip install python-telegram-bot requests apscheduler


Set up your credentials:

Open the main.py (or whichever filename you have) and find the following variables:

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"  # Insert your Telegram bot token
API_KEY = "YOUR_APRS_FI_API_KEY_HERE"  # Insert your aprs.fi API Key
Replace the placeholder values with your actual Telegram bot token and aprs.fi API key.


Run the bot:

python main.py

The bot will start polling for updates on Telegram.


Usage

Once the bot is running, you can interact with it on Telegram by sending commands (directly to the bot in a private chat, or in a group chat if you’ve invited it there). The most relevant commands are:

/start
Initializes the bot in the current chat.

/stop
Stops the periodic job in the current chat, so you no longer receive updates.

/setcallsign <callsign>
Changes the APRS callsign that this chat is tracking. For example:
/setcallsign IU1ABC-1
After issuing this command, the bot will start fetching data for the newly specified callsign.

/setinterval <seconds>
Changes the update interval (in seconds). 
For example:
/setinterval 1800
This sets the interval to 1800 seconds (i.e., 30 minutes). The bot will remove the old schedule and reschedule a new job for that chat at the new interval.


How the Bot Works

When you type /start, the bot looks up the current chat_id. It checks two dictionaries:

callsign_dict[chat_id] for the callsign.
interval_dict[chat_id] for the sending interval. 
If none exist, it sets them to default values and schedules a periodic job using Python Telegram Bot’s JobQueue.
The job runs the function send_aprs_summary(context) at the specified interval. 

This function:

- Retrieves the chat_id (from context.job.context) so it knows where to send the messages.
- Gets the callsign from callsign_dict[chat_id].
- Calls fetch_aprs_data(callsign), which makes two API calls to aprs.fi (one for location data, one for weather data).
- Combines the data into a formatted string and sends it to the chat.
- You can use /setcallsign and /setinterval at any time. When you change the interval, the old job is removed and a new job is scheduled with the updated interval. When you stop the bot with /stop, the job for that chat is removed.


File Overview

aprs_bot.py: The primary bot code. Contains:

- Global dictionaries callsign_dict and interval_dict to store data per chat.
- fetch_aprs_data() function to call aprs.fi’s API.
- Command handlers: /start, /stop, /setcallsign, /setinterval.
- A helper function schedule_job_for_chat() to manage scheduling with the JobQueue.
- The main() function which sets up the bot, registers handlers, and starts polling.

  
Troubleshooting

- If you don’t receive any messages in your Telegram chat:
- Double-check you typed /start in the correct chat (private or group).
- Verify that your APRS.fi API Key is correct and valid.
- Check the logs in your console for any Python errors or exceptions.
- If you see API-related errors, confirm you can reach https://api.aprs.fi/api/get from your environment (e.g., no firewall blocks) and that your APRS.fi key is active.


Contributing

Feel free to open issues or submit pull requests if you’d like to enhance this bot. You can improve:

- Error handling
- Data parsing or formatting
- Additional commands or features (e.g., storing and retrieving past data, or integrating with other services)
