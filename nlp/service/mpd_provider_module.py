from termcolor import colored
from nlp.service.response import Response, ErrorCodeEnum
from random import randint
from music_player.mpd_connection import ControlMPD
from music_player.load_mpd import LoadMPD
from time import sleep
from definitions import ROOT_DIR
import json

color = "green"

LoadMPD()

with open(ROOT_DIR + '/configs/configuration.json') as json_file:
    json_data = json.load(json_file)
try:
    mpdcontrol = ControlMPD(json_data['mpd']['server'], json_data['mpd']['port'])
except ConnectionRefusedError:
    print(colored("ConnectionRefusedError: check if your MPD server is running!", "red"))
    exit(0)


def trimGerne(gerne):
    # cut ' music' in the end
    music = "music"
    if gerne.lower().endswith(music):
        gerne = gerne[:len(gerne) - (len(music) + 1)]
    return gerne


def containsSongOrArtist(arguments):
    for argument in arguments:
        argument = argument.title()
        if mpdcontrol.is_artist_in_db(argument) or mpdcontrol.is_title_in_db(argument):
            return True
    return False


def playSongOrArtist(arguments):
    print(colored("RESULT: playSongOrArtist(" + ", ".join(arguments) + ")", color))
    for i in arguments:
        i = i.title()
        print(i)

        def play():
            mpdcontrol.play(song_pos)
            print(colored("\nCurrent Playlist: " + str(mpdcontrol.get_current_song_playlist()) + "\n", "yellow"))

        def check_numbers(artist):
            if mpdcontrol.get_number_artist_in_pl(artist=artist) < mpdcontrol.get_number_artist_in_db(artist=artist):
                mpdcontrol.add_artist_to_pl(artist=artist)
            else:
                return

        if mpdcontrol.is_artist_in_pl(i):
            print("Artist already in playlist")
            check_numbers(i)
            song_pos = mpdcontrol.get_desired_songpos(artist=i)
            play()
            break

        song_pos = mpdcontrol.add_artist_to_pl(i)
        print(song_pos)
        if song_pos is None:
            if mpdcontrol.is_title_in_pl(i):
                print("Title already in playlist")
                song_pos = mpdcontrol.get_desired_songpos(title=i)
                play()
                break
            song_pos = mpdcontrol.add_title_to_pl(i)

        if song_pos is not None:
            play()

def isGerne(gerne):
    gerne = trimGerne(gerne).lower()
    if mpdcontrol.is_genre_in_db(gerne):
        return True
    else:
        return False


def getRandomGenre():
    print("getRandomGenre")
    # genres = mpdcontrol.get_all_genres_in_db()

    gernes = ["rock", "hard rock", "alternative", "electro house"]
    return gernes[randint(0, len(gernes) - 1)]


# gernes is a list of gernes f. e. ['rock', 'electro house'] or ['rock']
def playGernes(gernes):
    print(colored("RESULT: playGernes(" + ", ".join(gernes) + ")", color))
    for i in gernes:
        song_pos = mpdcontrol.add_genre_to_pl(i)
        mpdcontrol.play(song_pos)
        print(mpdcontrol.get_current_song_playlist())
        sleep(10)


def stop():
    print(colored("RESULT: stop()", color))
    mpdcontrol.stop()


def pause():
    print(colored("RESULT: pause()", color))
    mpdcontrol.pause()


def resume():
    print(colored("RESULT: resume()", color))
    mpdcontrol.play()


def playOrResume():
    print(colored("RESULT: playOrResume()", color))


def playRandom():
    print(colored("RESULT: playRandom()", color))
    mpdcontrol.shuffle()
    mpdcontrol.set_random()
    mpdcontrol.play()


def playNext():
    print(colored("RESULT: playNext()", color))
    mpdcontrol.next()


def playPrevious():
    print(colored("RESULT: playPrevious()", color))
    mpdcontrol.previous()


def clearCurrentPlaylist():
    print(colored("RESULT: clearCurrentPlaylist()", color))
    mpdcontrol.clear_current_playlist()


def repeatPlaylist():
    print(colored("RESULT: repeatPlaylist()", color))
    mpdcontrol.set_repeat()


def repeatSong():
    print(colored("RESULT: repeatSong()", color))


def updateDatabase():
    print(colored("RESULT: updateDatabase()", color))
    mpdcontrol.update_database()


def speak(message):
    ## BING_KEY not known
    # tts = TextToSpeech(bing_key=BING_KEY, language='united_states', gender='Female')
    # resp = tts.request_to_bing(text=message)
    # tts.play_request(resp)
    print(colored("SPOKEN_Output: '" + message + "'", "red"))


def play_specific_song(song_name):
    def play():
        mpdcontrol.play(song_pos)

    if mpdcontrol.is_title_in_pl(song_name):
        song_pos = mpdcontrol.get_desired_songpos(title=song_name)
        play()
    else:
        song_pos = mpdcontrol.add_title_to_pl(song_name)
        play()


def add_playlist_to_queue(list_of_songsnames):
    """adds a list of songs to the queue and starts playing.
    Clears the previous queue. The first song in list_of_songnames is the first in the queue."""
    mpdcontrol.clear_current_playlist()
    for song in list_of_songsnames:
        mpdcontrol.add_title_to_pl(song)
    print(mpdcontrol.get_current_song_playlist())
    mpdcontrol.play(0)

