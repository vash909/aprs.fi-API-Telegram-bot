# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# aprs.fi API call
APRS_URL = "https://api.aprs.fi/api/get"
API_KEY = "YOUR_APRSFI_API_KEY"  # Replace with your aprs.fi API Key
FORMAT = "json"

# Global dictionaries (chat_id -> callsign) and (chat_id -> interval in seconds)
callsign_dict = {}
interval_dict = {}

def fetch_aprs_data(callsign: str) -> str:
    """Fetch APRS 'loc' and 'wx' data for a given callsign from aprs.fi."""
    try:
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

        loc_response = requests.get(APRS_URL, params=loc_params, timeout=10)
        loc_response.raise_for_status()
        loc_data = loc_response.json()

        wx_response = requests.get(APRS_URL, params=wx_params, timeout=10)
        wx_response.raise_for_status()
        wx_data = wx_response.json()

        if loc_data.get("entries") and wx_data.get("entries"):
            loc_entry = loc_data["entries"][0]
            wx_entry = wx_data["entries"][0]
            return (
                f"\U0001F30D Station: {loc_entry.get('name', 'N/A')}\n"
                f"\U0001F551 Local Time: {loc_entry.get('time', 'N/A')} epoch\n"
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
    except requests.Timeout:
        logging.error("Timeout fetching APRS data")
        return "Error: API request timed out."
    except Exception as e:
        logging.error(f"Error fetching APRS data: {e}")
        return f"Error: {e}"

def send_aprs_summary(context: CallbackContext):
    """Function called periodically by the JobQueue to fetch and send APRS data."""
    chat_id = context.job.context
    callsign = callsign_dict.get(chat_id, "IU1OLT-6")  #Default callsign, tribute to the wonderful wx station on the Monte Aiona summit
    summary = fetch_aprs_data(callsign)
    context.bot.send_message(chat_id=chat_id, text=summary)

def schedule_job_for_chat(chat_id: int, job_queue, interval: int):
    """Ensure jobs are removed before scheduling new ones."""
    # Remove all existing jobs for this chat_id
    old_jobs = job_queue.get_jobs_by_name(str(chat_id))
    for job in old_jobs:
        job.schedule_removal()
        logging.info(f"Removed old job for chat {chat_id}")

    # Schedule a new job
    job_queue.run_repeating(send_aprs_summary, interval=interval, first=0, context=chat_id, name=str(chat_id))
    logging.info(f"Scheduled new job for chat {chat_id} with interval {interval} seconds")

def start(update: Update, context: CallbackContext):
    """Handle /start command."""
    chat_id = update.message.chat_id

    if chat_id not in callsign_dict:
        callsign_dict[chat_id] = "IU1OLT-6" #Default callsign, tribute to the wonderful wx station on the Monte Aiona summit
    if chat_id not in interval_dict:
        interval_dict[chat_id] = 3600  # Default interval (1 hour)

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
    schedule_job_for_chat(chat_id, context.job_queue, interval_dict[chat_id])

def stop(update: Update, context: CallbackContext):
    """Handle /stop command."""
    chat_id = update.message.chat_id
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if jobs:
        for job in jobs:
            job.schedule_removal()
            logging.info(f"Stopped job for chat {chat_id}")
        update.message.reply_text("Bot stopped.")
    else:
        update.message.reply_text("No active jobs to stop.")

def set_callsign(update: Update, context: CallbackContext):
    """Handle /setcallsign command."""
    chat_id = update.message.chat_id
    if not context.args:
        update.message.reply_text("You must specify a callsign. Example: /setcallsign IU1BOT-5")
        return

    new_callsign = context.args[0].upper()
    callsign_dict[chat_id] = new_callsign
    update.message.reply_text(f"Callsign set to: {new_callsign}")
    logging.info(f"Updated callsign for chat {chat_id}: {new_callsign}")

def set_interval(update: Update, context: CallbackContext):
    """Handle /setinterval command."""
    chat_id = update.message.chat_id
    if not context.args:
        update.message.reply_text("You must specify the interval in seconds. Usage: /setinterval 1800")
        return

    try:
        new_interval = int(context.args[0])
    except ValueError:
        update.message.reply_text("Please provide a valid number (seconds).")
        return

    interval_dict[chat_id] = new_interval
    schedule_job_for_chat(chat_id, context.job_queue, new_interval)
    update.message.reply_text(f"Interval set to {new_interval} seconds.")
    logging.info(f"Updated interval for chat {chat_id}: {new_interval}")

def list_jobs(update: Update, context: CallbackContext):
    """List all active jobs for debugging."""
    jobs = context.job_queue.jobs()
    job_list = "\n".join([f"Job '{job.name}' for chat {job.context}: next run at {job.next_t}" for job in jobs])
    update.message.reply_text(f"Active jobs:\n{job_list}")
    logging.info(f"Active jobs: {job_list}")

def show_settings(update: Update, context: CallbackContext):
    """Show current settings for this chat."""
    chat_id = update.message.chat_id
    callsign = callsign_dict.get(chat_id, "Not Set")
    interval = interval_dict.get(chat_id, "Not Set")
    update.message.reply_text(f"Current settings:\nCallsign: {callsign}\nInterval: {interval}")
    logging.info(f"Chat {chat_id} settings: callsign={callsign}, interval={interval}")

def main():
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Replace with your bot token
    updater = Updater(TOKEN, use_context=True, workers=4)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CommandHandler("setcallsign", set_callsign))
    dispatcher.add_handler(CommandHandler("setinterval", set_interval))
    dispatcher.add_handler(CommandHandler("listjobs", list_jobs))
    dispatcher.add_handler(CommandHandler("showsettings", show_settings))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
