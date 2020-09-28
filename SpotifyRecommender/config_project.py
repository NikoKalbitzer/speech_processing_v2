import configparser
from pathlib import Path
import json

absolute_path = Path(__file__).parent
path_recommender_config = Path(__file__).parent / "config_recommender.ini"
config = configparser.ConfigParser()
config.read(path_recommender_config)

path_speech_processing_config = Path(__file__).parent / "../configs/configuration.json"
with open(path_speech_processing_config, "r") as json_file:
    data = json.load(json_file)

# [SPOTIFY]
CLIENT_ID = config.get("SPOTIFY", "CLIENT_ID")
CLIENT_SECRET = config.get("SPOTIFY", "CLIENT_SECRET")

# [MPD]
MPD_IP = data["mpd"]["server"]
MPD_PORT = data["mpd"]["port"]

# SAVE_PATH: Since these values should not be set by the user, they are set statically here
PATH_SONG_DATA = absolute_path / "song_tags.json"
PATH_RELATED_ARTISTS = absolute_path / "related_artists.json"
PATH_USER_DATA = absolute_path / "user_data.json"
