# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
from apscheduler.schedulers.background import BackgroundScheduler

# aprs.fi API call
APRS_URL = "https://api.aprs.fi/api/get"
API_KEY = "YOUR_APRSFI_API_KEY"  # Insert your aprs.fi API Key here
FORMAT = "json"

# Global dictionaries (chat_id -> callsign) and (chat_id -> interval in seconds)
callsign_dict = {}
interval_dict = {}

def fetch_aprs_data(callsign: str) -> str:
    """Fetch APRS 'loc' and 'wx' data for a given callsign from aprs.fi."""
    loc_params = {
        "name": callsign,
        "what": "loc",
        "apikey": API_KEY,
        "format": FORMAT
    }
    wx_params = {
        "name": callsign,
        "what": "wx",
        "apikey": API_KEY,
        "format": FORMAT
    }

    try:
        # Request location data
        loc_response = requests.get(APRS_URL, params=loc_params)
        loc_response.raise_for_status()
        loc_data = loc_response.json()

        # Request weather data
        wx_response = requests.get(APRS_URL, params=wx_params)
        wx_response.raise_for_status()
        wx_data = wx_response.json()

        # Combine both location and weather data
        if loc_data.get("entries") and wx_data.get("entries"):
            loc_entry = loc_data["entries"][0]
            wx_entry = wx_data["entries"][0]
            return (
                f"\U0001F30D Station: {loc_entry.get('name', 'N/A')}\n"
                f"\U0001F551 Last packet: {loc_entry.get('time', 'N/A')} epoch\n"
                f"\U0001F4CD Latitude: {loc_entry.get('lat', 'N/A')}\n"
                f"\U0001F4CD Longitude: {loc_entry.get('lng', 'N/A')}\n"
                f"\U0001F3D4 Altitude: {loc_entry.get('altitude', 'N/A')} m\n"
                f"\U0001F4E1 Path: {loc_entry.get('path', 'N/A')}\n"
                f"\U0001F4AC Comment: {loc_entry.get('comment', 'N/A')}\n"
                f"--- \U0001F327 Weather Data ---\n"
                f"\U0001F321 Temperature: {wx_entry.get('temp', 'N/A')} °C\n"
                f"\U0001F4A7 Humidity: {wx_entry.get('humidity', 'N/A')}%\n"
                f"\U0001F535 Pressure: {wx_entry.get('pressure', 'N/A')} hPa\n"
                f"\U0001F32C Wind Speed: {wx_entry.get('wind_speed', 'N/A')} km/h\n"
                f"\U0001F9ED Wind Direction: {wx_entry.get('wind_direction', 'N/A')}°"
            )
        else:
            return "No data available for this station."
    except Exception as e:
        return f"Error fetching data: {e}"

def send_aprs_summary(context: CallbackContext):
    """Function called periodically by the JobQueue to fetch and send APRS data."""
    chat_id = context.job.context
    
    # Get the stored callsign and interval for this chat; set defaults if not available
    callsign = callsign_dict.get(chat_id, "N0CALL-99")
    summary = fetch_aprs_data(callsign)
    context.bot.send_message(chat_id=chat_id, text=summary)

def schedule_job_for_chat(chat_id: int, job_queue, interval: int):
    """
    Helper function that removes any existing jobs for `chat_id`
    and schedules a new one with the specified `interval`.
    """
    # Remove old jobs with the name = str(chat_id)
    old_jobs = job_queue.get_jobs_by_name(str(chat_id))
    for job in old_jobs:
        job.schedule_removal()
    
    # Schedule the new job
    job = job_queue.run_repeating(send_aprs_summary, interval=interval, first=0, context=chat_id)
    job.name = str(chat_id)

def start(update: Update, context: CallbackContext):
    """/start command to initialize the bot and schedule the periodic job."""
    chat_id = update.message.chat_id

    # Set default callsign and default interval if not already set
    if chat_id not in callsign_dict:
        callsign_dict[chat_id] = "N0CALL-99"
    if chat_id not in interval_dict:
        interval_dict[chat_id] = 3600  # default interval = 3600 seconds (1 hour)

    context.bot.send_message(
        chat_id=chat_id, 
        text=(
            "Bot started!\n"
            f"Current callsign: {callsign_dict[chat_id]}\n"
            f"Current interval: {interval_dict[chat_id]} seconds\n\n"
            "Use /setcallsign <callsign> to change the callsign.\n"
            "Use /setinterval <seconds> to change the interval."
        )
    )

    # Schedule the job using the stored interval
    schedule_job_for_chat(chat_id, context.job_queue, interval_dict[chat_id])

def stop(update: Update, context: CallbackContext):
    """/stop command to remove the periodic job."""
    chat_id = update.message.chat_id
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in jobs:
        job.schedule_removal()
    update.message.reply_text("Bot stopped.")

def set_callsign(update: Update, context: CallbackContext):
    """
    /setcallsign <callsign>
    Let the user change the callsign for the current chat.
    """
    chat_id = update.message.chat_id
    
    # If user doesn't provide a callsign, remind them
    if not context.args:
        update.message.reply_text("You must specify a callsign. Usage: /setcallsign <callsign>")
        return
    
    new_callsign = context.args[0].upper()
    callsign_dict[chat_id] = new_callsign
    
    update.message.reply_text(f"Callsign set to: {new_callsign}")

def set_interval(update: Update, context: CallbackContext):
    """
    /setinterval <seconds>
    Let the user change the sending interval for the current chat.
    """
    chat_id = update.message.chat_id

    if not context.args:
        update.message.reply_text("You must specify the interval in seconds. Usage: /setinterval 1800")
        return
    
    # Try to parse the interval as an integer
    try:
        new_interval = int(context.args[0])
    except ValueError:
        update.message.reply_text("Please provide a valid number (seconds).")
        return

    # Update the interval in our dictionary
    interval_dict[chat_id] = new_interval
    
    # Reschedule the job with the new interval
    schedule_job_for_chat(chat_id, context.job_queue, new_interval)

    update.message.reply_text(f"Interval set to {new_interval} seconds.")

def main():
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Insert your Telegram bot token here
    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CommandHandler("setcallsign", set_callsign))
    dispatcher.add_handler(CommandHandler("setinterval", set_interval))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
