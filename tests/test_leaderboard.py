import pytest
from datetime import datetime
import json
from leaderboard import AoCLeaderboard

@pytest.fixture
def mock_leaderboard():
    return AoCLeaderboard(
        session_token="fake_token",
        leaderboard_id="123456",
        year=2023
    )

@pytest.fixture
def sample_leaderboard_data():
    return {
        "members": {
            "12345": {
                "name": "Test User",
                "stars": 6,
                "local_score": 100,
                "completion_day_level": {
                    "1": {
                        "1": {"get_star_ts": "1701432000"},
                        "2": {"get_star_ts": "1701435600"}
                    },
                    "2": {
                        "1": {"get_star_ts": "1701518400"},
                        "2": {"get_star_ts": "1701522000"}
                    }
                }
            }
        }
    }

def test_check_for_new_stars(mock_leaderboard, sample_leaderboard_data):
    # Test checking for new stars after a given timestamp
    last_check_time = 1701430000  # Before first star
    new_achievements = mock_leaderboard.check_for_new_stars(
        sample_leaderboard_data, 
        last_check_time
    )
    assert len(new_achievements) == 4
    assert "Test User" in new_achievements[0]["message"]
    assert "Day 1 Part 1" in new_achievements[0]["message"]

def test_format_leaderboard(mock_leaderboard, sample_leaderboard_data):
    formatted = mock_leaderboard.format_leaderboard(sample_leaderboard_data)
    assert "Test User" in formatted
    assert "6⭐" in formatted
    assert "Score: 100" in formatted 