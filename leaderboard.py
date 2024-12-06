import asyncio
from datetime import datetime
import json
import aiohttp
from config import CACHE_TTL

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
                    print("Using cached leaderboard data")
                    return cache_data.get("data")
                else:
                    print("Cache expired")
                    return None
        except (FileNotFoundError, json.JSONDecodeError):
            print("No valid cache found")
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
                    print("Fetched fresh leaderboard data and updated cache")
                    return data
                print(f"Failed to fetch leaderboard data: {response.status}")
                return None

    def format_leaderboard(self, data):
        """Format leaderboard data into a readable message"""
        users = []
        current_day = datetime.now().day

        # Define star symbols with consistent width
        BOTH_STARS = "★"    # Full star
        ONE_STAR = "☆"      # Hollow star
        NO_STARS = "·"      # Middle dot (or could use "░" for a block)

        # Get max name length for padding
        max_name_length = 0
        for member_data in data["members"].values():
            name = member_data.get("name", "Anonymous")
            if member_data.get("stars", 0) > 0:  # Only consider active users
                max_name_length = max(max_name_length, len(name))

        # Add padding to ensure alignment
        name_padding = max_name_length + 2  # Add some extra space
        
        for member_id, member_data in data["members"].items():
            name = member_data.get("name", "Anonymous")
            stars = member_data.get("stars", 0)
            local_score = member_data.get("local_score", 0)
            
            if stars == 0:
                continue
                
            day_status = []
            completion_data = member_data.get("completion_day_level", {})
            
            for day in range(1, current_day + 1):
                day_info = completion_data.get(str(day), {})
                if "2" in day_info:
                    day_status.append(BOTH_STARS)
                elif "1" in day_info:
                    day_status.append(ONE_STAR)
                else:
                    day_status.append(NO_STARS)
            
            users.append((name, stars, local_score, day_status))
        
        users.sort(key=lambda x: (-x[1], -x[2], x[0]))
        
        # Format day numbers vertically for two digits
        day_numbers_top = []
        day_numbers_bottom = []
        for day in range(1, current_day + 1):
            if day < 10:
                day_numbers_top.append(" ")
                day_numbers_bottom.append(str(day))
            else:
                day_numbers_top.append(str(day)[0])    # First digit
                day_numbers_bottom.append(str(day)[1])  # Second digit
        
        lines = ["**🎄 Advent of Code Leaderboard 🎄**\n"]
        
        # Add day numbers in two rows for double digits
        lines.append(f"```\n{'Day':<{max_name_length}}  {' '.join(day_numbers_top)}")
        lines.append(f"{'':<{max_name_length}}  {' '.join(day_numbers_bottom)}")
        
        # Create separator line that matches the header
        separator_length = max_name_length + 2 + current_day * 2  # name width + 2 spaces + day columns
        lines.append("-" * separator_length)
        
        # Format each user's line with proper padding
        for i, (name, stars, score, day_status) in enumerate(users, 1):
            status_line = " ".join(day_status)
            # Pad the name to align all status indicators
            padded_name = f"{name:<{max_name_length}}"
            lines.append(f"{padded_name}  {status_line}  ({stars}⭐ Score: {score})")
        
        lines.append("```")
        return "\n".join(lines)

    def check_for_new_stars(self, data, last_check_time):
        """Check for new stars since last check"""
        new_achievements = []
        current_time = int(datetime.now().timestamp())

        for member_id, member_data in data["members"].items():
            member_name = member_data.get("name", "Anonymous")
            print(f"Checking stars for {member_name}")

            for day, stars in member_data["completion_day_level"].items():
                for star_num, star_data in stars.items():
                    star_time = int(star_data["get_star_ts"])

                    if star_time > last_check_time:
                        new_achievements.append({
                            "time": star_time,
                            "message": f"🌟 **{member_name}** completed Day {day} Part {star_num} at <t:{star_time}:t>!"
                        })
                        print(f"Found new star: Day {day} Part {star_num} by {member_name}")

        return sorted(new_achievements, key=lambda x: x["time"]) 

async def test_leaderboard():
    """Test function to fetch and display the leaderboard"""
    from config import AOC_SESSION_TOKEN, AOC_LEADERBOARD_ID, AOC_YEAR
    import asyncio

    # Create leaderboard instance
    leaderboard = AoCLeaderboard(
        session_token=AOC_SESSION_TOKEN,
        leaderboard_id=AOC_LEADERBOARD_ID,
        year=AOC_YEAR
    )

    # Fetch and display data
    data = await leaderboard.fetch_data(force_fresh=True)
    if data:
        print("\nFormatted Leaderboard:")
        print(leaderboard.format_leaderboard(data))
    else:
        print("Failed to fetch leaderboard data")

if __name__ == "__main__":
    # Run the test function
    asyncio.run(test_leaderboard()) 