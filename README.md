# Advent of Code Discord Bot

A Discord bot that tracks and announces progress on Advent of Code leaderboards.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `config.py` file with your settings:
   ```python
   TOKEN = "your-discord-bot-token"
   AOC_SESSION_TOKEN = "your-aoc-session-token"
   AOC_LEADERBOARD_ID = "your-leaderboard-id"
   AOC_YEAR = 2024
   TESTING_MODE = False
   CACHE_TTL = 900  # 15 minutes in seconds
   ```
5. Run the bot:
   ```bash
   python bot.py
   ```

## Features

- Tracks Advent of Code progress
- Announces new stars and achievements
- Shows leaderboard with `/leaderboard` command
- Testing mode for development 

## Testing

This project uses pytest for testing. To run the tests:

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
2. Run the tests:
   ```bash
   pytest
   ``` 