import asyncio
from datetime import datetime
import json
import aiohttp
from config import CACHE_TTL
import logging

logger = logging.getLogger('AoCBot')

class AoCLeaderboard:
    def __init__(self, session_token, leaderboard_id, year):
        self.session_token = session_token
        self.leaderboard_id = leaderboard_id
        self.year = year
        self.CACHE_TTL = CACHE_TTL
        self.LEADERBOARD_URL = f"https://adventofcode.com/{year}/leaderboard/private/view/{leaderboard_id}.json"
        self.LEADERBOARD_CACHE_FILE = "leaderboard_cache.json"

    def read_cache(self):
        """Read cached leaderboard data if it exists and is fresh"""
        try:
            with open(self.LEADERBOARD_CACHE_FILE, "r") as f:
                cache_data = json.load(f)
                cache_time = cache_data.get("timestamp", 0)

                if (datetime.now().timestamp() - cache_time) < self.CACHE_TTL:
                    logger.info("Using cached leaderboard data")
                    return cache_data.get("data")
                else:
                    logger.info("Cache expired")
                    return None
        except (FileNotFoundError, json.JSONDecodeError):
            logger.info("No valid cache found")
            return None

    def save_cache(self, data):
        """Save leaderboard data to cache file"""
        cache_data = {"timestamp": datetime.now().timestamp(), "data": data}
        with open(self.LEADERBOARD_CACHE_FILE, "w") as f:
            json.dump(cache_data, f)

    async def fetch_data(self, force_fresh=False):
        """Fetch data from AoC leaderboard with caching"""
        if not force_fresh:
            cached_data = self.read_cache()
            if cached_data:
                return cached_data

        headers = {
            "Cookie": f"session={self.session_token}",
            "User-Agent": "github.com/yourusername/aoc-discord-bot by your@email.com",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.LEADERBOARD_URL, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.save_cache(data)
                    logger.info("Fetched fresh leaderboard data and updated cache")
                    return data
                logger.error(f"Failed to fetch leaderboard data: {response.status}")
                return None

    def check_for_new_stars(self, data, last_check_time):
        """Check for new stars since last check"""
        new_achievements = []
        current_time = int(datetime.now().timestamp())

        for member_id, member_data in data["members"].items():
            member_name = member_data.get("name", "Anonymous")
            logger.debug(f"Checking stars for {member_name}")

            for day, stars in member_data["completion_day_level"].items():
                for star_num, star_data in stars.items():
                    star_time = int(star_data["get_star_ts"])

                    if star_time > last_check_time:
                        new_achievements.append({
                            "time": star_time,
                            "message": f"🌟 **{member_name}** completed Day {day} Part {star_num} at <t:{star_time}:t>!"
                        })
                        logger.info(f"Found new star: Day {day} Part {star_num} by {member_name}")

        return sorted(new_achievements, key=lambda x: x["time"])

async def test_leaderboard():
    """Test function to fetch and display the leaderboard"""
    from config import AOC_SESSION_TOKEN, AOC_LEADERBOARD_ID, AOC_YEAR
    import asyncio

    # Set up logging for test function
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create leaderboard instance
    leaderboard = AoCLeaderboard(
        session_token=AOC_SESSION_TOKEN,
        leaderboard_id=AOC_LEADERBOARD_ID,
        year=AOC_YEAR
    )

    # Fetch and display data
    data = await leaderboard.fetch_data(force_fresh=True)
    if data:
        logger.info("\nFormatted Leaderboard:")
        logger.info(leaderboard.format_leaderboard(data))
    else:
        logger.error("Failed to fetch leaderboard data")

if __name__ == "__main__":
    # Run the test function
    asyncio.run(test_leaderboard()) 