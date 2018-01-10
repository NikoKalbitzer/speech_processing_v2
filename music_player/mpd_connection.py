import threading
from mpd import MPDClient
from time import sleep


class ControlMPD:

    def __init__(self, host, port=None):
        """
        Creates a MPD client to control

        :param host: hostname for the MPD server
        :param port: port to communicate with the MPD server
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
        self.__thread = None
        self.__running = False
        self.start()

    def __del__(self):
        """
        Destructor
        """
        self.stop_thread()
        self.connected = False
        self.client.close()
        self.client.disconnect()

    def stop_thread(self):
        """
        method to stop the thread
        """
        if self.__thread is not None:
            self.__running = False
            self.__thread.join()
            self.__thread = None

    def start(self, as_daemon=None):
        """
        method to start the __run thread

        as_daemon: boolean attribute to run the thread as daemon or not
        """
        if self.__thread is None:
            self.__running = True
            self.__thread = threading.Thread(target=self.__run)
            # default behavior run thread as daemon
            if as_daemon is None:
                self.__thread.daemon = True
            else:
                if not isinstance(as_daemon, bool):
                    raise TypeError("'as_daemon' must be a boolean type")
                else:
                    self.__thread.daemon = as_daemon
            self.__thread.start()

    def __run(self):
        """
        daemon thread to ping to the mpd client
        """
        while self.__running:
            self.client.ping()
            sleep(55)

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

    def add_artist_to_pl(self, artist, new_playlist=False):
        """
        Find artist in db and adds them to the current/new playlist

        :param artist: artist_string to add to playlist
        :param new_playlist: False as default, Yes, create new playlist
        :return: song_pos to play for, if selected artist in database
                 None, if selected artist not in database
        """
        if isinstance(artist, str):
            resp_artist = self.client.find("Artist", artist)
            if len(resp_artist) == 0:
                song_pos = self.advanced_search_in_db(artist)
                if song_pos is None:
                    return None
                else:
                    return song_pos
            else:
                if new_playlist is False:
                    song_pos = self.get_current_songpos()
                    #if song_pos is None:
                    #    song_pos = 0
                    self.client.findadd("Artist", artist)
                else:
                    self.clear_current_playlist()
                    self.client.findadd("Artist", artist)
                    song_pos = 0

                return song_pos
        else:
            raise TypeError("'artist' must be Type of String")

    def add_title_to_pl(self, title):
        """
        Add desired genre to playlist, if genre is in db available

        :param title: title_string to add to playlist
        :return: song_pos to play for, if selected title in database
                 None, if selected title not in database

        """
        if isinstance(title, str):
            resp_title = self.client.find("Title", title)
            if len(resp_title) == 0:
                song_pos = self.advanced_search_in_db(title)
                if song_pos is None:
                    return None
                else:
                    return song_pos
            else:
                song_pos = self.get_current_songpos()
                self.client.findadd("Title", title)
                return song_pos

        else:
            raise TypeError("'title must be Type of String")

    def add_genre_to_pl(self, genre, new_playlist=False):
        """
        Add desired genre to playlist, if genre is in db available

        :param genre: genre_string to add to playlist
        :param new_playlist: False as default, Yes, create new playlist
        :return: song_pos to play for, if selected genre in database
                 None, if selected genre not in database
        """
        if isinstance(genre, str):
            resp_genre = self.client.find("Genre", genre)
            if len(resp_genre) == 0:
                song_pos = self.advanced_search_in_db(genre)
                if song_pos is None:
                    return None
                else:
                    return song_pos
            else:
                if new_playlist is False:
                    song_pos = self.get_current_songpos()
                    self.client.findadd("Genre", genre)
                else:
                    self.clear_current_playlist()
                    self.client.findadd("Genre", genre)
                    song_pos = 0
                return song_pos
        else:
            raise TypeError("'genre' must be Type of String")

    def advanced_search_in_db(self, search_str, search_type=None, s_pos=True):
        """
        search for specific string in database
        search_type can be any, Artist, Title, Genre..

        :param search_str: string to search in database
        :param search_type: string, "any", "Artist", "Title", "Genre" ..
        :param s_pos: boolean, if True, it will be returned song_pos and db_response
                               if False, it will be returned only db_response
        :return: None, if no match were found
                 song_pos for the 'play method' to play the requested string
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        if isinstance(search_str, str):
            if search_type is None:
                db_response = self.client.search("any", search_str)
            else:
                if isinstance(search_type, str):
                    db_response = self.client.search(search_type, search_str)
                else:
                    raise TypeError("'type' must be Type of String")
            if len(db_response) == 0:
                return None
            elif s_pos is False:
                return db_response
            else:
                song_pos = self.get_current_songpos()
                for resp in db_response:
                    self.client.add(resp.get('file'))
                if song_pos is None:
                    song_pos = 0
                    return song_pos
                else:
                    return song_pos
        else:
            raise TypeError("'search_str' must be Type of String")

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

    def get_tagtypes(self):
        """
        get the available tagtypes from the mpd server

        :return: list containing available tagtypes
                 ['Artist', 'Album', 'Title', 'Track', 'Name', 'Genre', 'Date', 'Composer', 'Performer', 'Disc']
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        return self.client.tagtypes()

    def get_current_songpos(self):
        """

        :return:
        """
        if not self.connected:
            raise ConnectionError("mpd client lost the connection")

        pos_list = [pos.get('pos') for pos in self.client.playlistid()]
        pos_list = [int(pos) for pos in pos_list]
        if len(pos_list) > 0:
            return int(max(pos_list)) + 1
        else:
            return 0

    def get_all_artists_in_db(self):
        """
        method to get all artists in database

        :return: list, that contains all artists from database
        """

        return [artist.get('artist') for artist in self.client.listallinfo() if artist.get('artist') is not None]

    def get_all_titles_in_db(self):
        """
        method to get all titles in database

        :return: list, that contains all titles from database
        """
        return [title.get('title') for title in self.client.listallinfo() if title.get('title') is not None]

    def get_all_genres_in_db(self):
        """
        method to get all genres in database

        :return: list, that contains all genres from database
        """
        return [genre.get('genre') for genre in self.client.listallinfo() if genre.get('genre') is not None]

    def is_artist_in_db(self, artist):
        """
        boolean method to check, if desired artist is in db available

        :param artist: string, artist to search for
        :return: True, if artist is available
                 False, if artist is not available
        """
        resp_artist = self.client.find("Artist", artist)
        print(resp_artist)
        if len(resp_artist) > 0:
            return True
        else:
            db_response = self.advanced_search_in_db(search_str=artist, search_type="Artist", s_pos=False)
            if db_response is None:
                return False
            else:
                if len(db_response) > 0:
                    return True
                else:
                    return False

    def is_title_in_db(self, title):
        """
        boolean method to check, if desired title is in db available

        :param title: string, title to search for
        :return: True, if title is available
                 False, if title is not available
        """
        resp_title = self.client.find("title", title)
        if len(resp_title) > 0:
            return True
        else:
            db_response = self.advanced_search_in_db(search_str=title, search_type="title", s_pos=False)
            if db_response is None:
                return False
            else:
                if len(db_response) > 0:
                    return True
                else:
                    return False

    def is_genre_in_db(self, genre):
        """
        boolean method to check, if desired genre is in db available

        :param genre: string, genre to search for
        :return: True, if genre is available
                 False, if genre is not available
        """
        resp_genre = self.client.find("genre", genre)
        if len(resp_genre) > 0:
            return True
        else:
            db_response = self.advanced_search_in_db(search_str=genre, search_type="genre", s_pos=False)
            if db_response is None:
                return False
            else:
                if len(db_response) > 0:
                    return True
                else:
                    return False

# CURRENT PLAYLIST

    def add_song_to_playlist(self, song):
        """

        :param song:
        :return:
        """
        if isinstance(song, str):
            self.client.add(song)

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
    #mpdclient = ControlMPD("localhost", 6600)
    mpdclient.play()
    sleep(10)
    mpdclient.stop()


