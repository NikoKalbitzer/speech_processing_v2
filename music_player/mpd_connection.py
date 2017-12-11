from mpd import MPDClient
from time import sleep


class ControlMPD:

    def __init__(self, host, port=None):
        """

        :param host:
        :param port:
        """
        if isinstance(host, str):
            self.host = host
        else:
            raise TypeError("'host' must be Type of String")

        if port is None:
            self.port = 6600
        else:
            if isinstance(port, int):
                self.port = port
            else:
                raise TypeError('port must be Type of Int')

        self.client = MPDClient()
        self.client.connect(host, port)
        self.connected = True

    def __del__(self):
        """
        Destructor
        """
        self.connected = False
        self.client.close()
        self.client.disconnect()

    def match_in_database(self, match_str):
        """

        :return:
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        if isinstance(match_str, str):
            db_response = self.client.search('any', match_str)
        else:
            raise TypeError("'match_str' must be Type of String")

        for resp in db_response:
            file = resp.get('file')
            self.client.add(file)
        current_playlist = self.get_current_song_playlist()
        songpos = len(current_playlist) - len(db_response)
        return songpos

    def update_database(self):
        """
        when changes in music folder were made, update the database
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")
        else:
            self.client.update()
            return True

    def create_music_playlist(self):
        """
        creates the music playlist for all songs the music folder contains
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")
        if self.clear_current_playlist():
            if self.update_database():
                music_list = self.client.listall()
                all_songs = list()
                for file in range(0, len(music_list)):
                    single_song = music_list[file].get("file")
                    self.client.add(single_song)
                    all_songs.append(single_song)
                return all_songs


# QUERYING USEFUL INFORMATION

    def get_current_song(self):
        """
        displays the song info of the current song
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        return self.client.currentsong()

    def get_current_song_playlist(self):
        """
        displays the current playlist
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        return self.client.playlist()

    def get_player_status(self):
        """
        reports the current status of the player and the volume level
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        return self.client.status()


# PLAYBACK OPTIONS

    def set_random(self):
        """
        sets random state ON or OFF
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        state = self.get_player_status()
        random_state = state.get('random')

        if random_state == '0':
            self.client.random(1)
        else:
            self.client.random(0)

    def set_repeat(self):
        """
        sets repeat state ON or OFF
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        state = self.get_player_status()
        repeat_state = state.get('repeat')

        if repeat_state == '0':
            self.client.repeat(1)
        else:
            self.client.repeat(0)

# CURRENT PLAYLIST

    def clear_current_playlist(self):
        """
        clears the current playlist
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")
        else:
            self.client.clear()
            return True

    def delete_song(self, songid=None):
        """
        deletes a song from the playlist
        :param songid:
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        if songid is None:
            self.client.delete()
        else:
            self.client.deleteid(songid)


# CONTROLLING PLAYBACK

    def pause(self):
        """
        toggles pause/ resume playing
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        states = self.get_player_status()
        player_state = states.get('state')

        if player_state == 'play':
            self.client.pause(1)
        elif player_state == 'pause':
            self.client.pause(0)
        else:
            print("state: stop is active")

    def shuffle(self):
        """
        shuffles the current playlist
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")
        else:
            self.client.shuffle()

    def play(self, songpos=None):
        """
        starts playing
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        if songpos is None:
            self.client.play()
        else:
            self.client.play(songpos)

    def stop(self):
        """
        stops playing
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")
        else:
            self.client.stop()

    def next(self):
        """
        plays next song in the playlist
        """

        if not self.connected:
            raise ConnectionError("mpd client lost the connection")
        else:
            self.client.next()

    def previous(self):
        """
        plays previous song in the playlist
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")
        else:
            self.client.previous()


if __name__ == "__main__":

    mpdclient = ControlMPD("192.168.178.37", 6600)
    #mpdclient.clear_current_playlist()
    #mpdclient.match_in_database()
    #print(mpdclient.get_current_song_playlist())
    #mpdclient.play(2)
    #sleep(10)
    mpdclient.stop()

