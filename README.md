# APRS Telegram Bot

This repository contains a Telegram bot that fetches APRS data from [aprs.fi](https://aprs.fi/) and sends periodic updates to a Telegram chat. The bot allows users to set their own APRS callsign and update interval, making it customizable for different use cases.

---

## Features

- **APRS Data Fetching**:
  - Retrieves **location** (`loc`) and **weather** (`wx`) data from the [aprs.fi API](https://aprs.fi/page/api).
  - Combines both data types into a single, formatted message.

- **Customizable Settings**:
  - **Callsign**: Each chat can set its own callsign using `/setcallsign <callsign>`.
  - **Update Interval**: Configure the frequency of updates in seconds using `/setinterval <seconds>`.

- **Per-Chat Isolation**:
  - Each chat has its own settings and independent scheduled jobs.

- **Interactive Commands**:
  - Start, stop, and manage the bot via simple Telegram commands.
  - /start - Starts the bot
  - /stop - Stops the bot
  - /setinterval - set the interval between messages (in seconds)
  - /setcallsign  - set the callsign to fetch

- **Debugging Tools**:
  - View active jobs and current settings for debugging and monitoring.
