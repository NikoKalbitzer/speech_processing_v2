from mpd import MPDClient
from time import sleep
import os

class SongControl(object):

    def __init__(self, host, port=None):

        self.host = host
        if port is None:
            self.port = 6600
        else:
            self.port = port

        self.client = MPDClient()
        self.playlist = None

        if self.host and self.port is not None:
            self.client.connect(host, port)
            self.connected = True
        else:
            self.connected = False

    def __del__(self):
        """
        Destructor
        """
        self.connected = False
        self.client.close()
        self.client.disconnect()

    def update_database(self):
        """
        when changes in music folder were made, update the database
        """
        if not self.connected:
            return None
        else:
            response = self.client.update()
            return response

    def create_music_playlist(self):
        """
        creates the music playlist for all songs the music folder contains
        """
        if not self.connected:
            return None
        if self.clear_current_playlist():
            if self.update_database():
                music_list = self.client.listall()
                all_songs = list()
                for file in range(0, len(music_list)):
                    single_song = music_list[file].get("file")
                    self.client.add(single_song)
                    all_songs.append(single_song)
                return all_songs

    def create_stream_playlist(self):
        """
        creates the stream playlist for all radio streams the playlist folder contains
        """
        if not self.connected:
            return None
        if self.clear_current_playlist():
            if self.update_database():
                state = self.get_list_of_playlists()
                all_playlists = list()
                for i in range(0, len(state)):
                    single_playlist = state[i].get("playlist")
                    self.client.load(single_playlist)
                    all_playlists.append(single_playlist)
                return all_playlists

# QUERYING USEFUL INFORMATION

    def get_current_song(self):
        """
        displays the song info of the current song
        """
        if not self.connected:
            return None

        return self.client.currentsong()

    def get_current_song_playlist(self):
        """
        displays the current playlist
        """
        if not self.connected:
            return None

        return self.client.playlist()

    def get_player_status(self):
        """
        reports the current status of the player and the volume level
        """
        if not self.connected:
            return None

        return self.client.status()


# PLAYBACK OPTIONS
    # TODO
    def volume_full(self):
        """
         set volume in range of 0-100
        """
        if not self.connected:
            return None
        os.system("amixer cset numid=1 207")

    def volume_middle(self):
        """
         set volume in range of 0-100
        """
        if not self.connected:
            return None
        os.system("amixer cset numid=1 130")

    def volume_mute(self):
        """
         set volume in range of 0-100
        """
        if not self.connected:
            return None
        os.system("amixer cset numid=1 0")

    def set_random(self):
        """
        sets random state ON or OFF
        """
        if not self.connected:
            return None

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
            return None

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
            return None
        else:
            self.client.clear()
            return True

    def delete_song(self, songid=None):
        """
        deletes a song from the playlist
        :param songid:
        """
        if not self.connected:
            return None

        if songid is None:
            self.client.delete()
        else:
            self.client.deleteid(songid)

# STORED PLAYLISTS IN FOLDER PLAYLISTS

    def get_list_of_playlists(self):
        """
        prints a list of the playlist folder
        """
        if not self.connected:
            return None

        return self.client.listplaylists()

# CONTROLLING PLAYBACK

    def pause(self):
        """
        toggles pause/ resume playing
        """
        if not self.connected:
            return None

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
            return None
        else:
            self.client.shuffle()

    def play(self, songpos=None):
        """
        starts playing
        """
        if not self.connected:
            return None

        if songpos is None:
            self.client.play()
        else:
            self.client.play(songpos)

    def stop(self):
        """
        stops playing
        """
        if not self.connected:
            return None
        else:
            self.client.stop()

    def next(self):
        """
        plays next song in the playlist
        """

        if not self.connected:
            return None
        else:
            self.client.next()

    def previous(self):
        """
        plays previous song in the playlist
        """
        if not self.connected:
            return None
        else:
            self.client.previous()




"""

if __name__ == "__main__":

    s = SongControl("localhost", 6600)
    print(s.get_player_status())
    #d = s.create_stream_playlist()
    #print(d)
    #s.clear_current_playlist()
    #d = s.create_music_playlist()
    #print(d)
    #s.set_random()
    #s.play()
    #print(s.get_currentsong())
    #print(s.get_player_status())
    #s.set_repeat()
    #sleep(10)
    #s.pause()
    #print(s.get_current_song_playlist())
    #s.next()
    #s.set_volume(80)
    #sleep(10)
    s.stop()

"""
