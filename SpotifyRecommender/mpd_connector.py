from mpd import MPDClient


class MpdConnector:
    def __init__(self, mpd_ip="localhost", mpd_port=6600):
        self.mpd_ip = mpd_ip
        self.mpd_port = mpd_port
        self.client = self._connect_to_mpd()

    def _connect_to_mpd(self):
        client = MPDClient()
        client.timeout = 10
        client.idletimeout = None
        client.connect(self.mpd_ip, self.mpd_port)
        return client

    def get_current_song(self):
        """
        return the currently played song
        :return: dict of info of currently played song. relevant keys: title, artist, genre
        """
        return self.client.currentsong()

    def get_all_songs(self):
        """
        :return: List of all songs: ["title": song["title"], "artist": song["artist"]}, {...}]
        """
        all_songs = self.client.listallinfo()
        reduced_dict_list = []
        incomplete_metadata = []
        for song in all_songs:
            try:
                reduced_dict_list.append(
                    {"title": song["title"], "artist": song["artist"], "genre": song["genre"], "date": song["date"],
                     "album": song["album"]})
            except KeyError:
                if "directory" not in song:  # filter out directories
                    incomplete_metadata.append(song)
        #print(colored("Incomplete Metadata found for: " + str(len(incomplete_metadata)) + " songs", "yellow"))
        print(len(reduced_dict_list), "songs with complete metadata found in your MPD media library.")
        return reduced_dict_list

    def play_next_song(self):
        """for testing purposes only"""
        self.client.play()
        self.client.next()
        print("next song playing")

    def play_specific_song(self, songname):
        self.client.play(songname)

    def pause(self):
        self.client.pause()

    def update_database(self):
        self.client.update()
        print("updated database")


def test_mpd():
    mpd_connector = MpdConnector("localhost", 6600)
    mpd_connector.update_database()
    print(mpd_connector.get_current_song())
    print(mpd_connector.get_all_songs())
