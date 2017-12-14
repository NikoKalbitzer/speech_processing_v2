from termcolor import colored
from MPD_NLP.service.response import Response, ErrorCodeEnum
from random import randint
from music_player.mpd_connection import ControlMPD
color = "green"

gernes = ["rock", "hard rock", "alternative", "electro house"]
songs = [ "heroes" ]
artists = [ "david bowie", "five finger death punch", "alan walker"]

# not working for now - ConnectionRefusedError: [Errno 111] Connection refused
mpdcontrol = ControlMPD("192.168.178.37", 6600)
mpdcontrol.start()

def playGerneSongArtist(arguments):
    # determine if this chunks are gernes, artists or songs
    # for gerne:
    # should be only chunks with one gerne or <GERNE> + music
    # if there are some gerne chunks and a artist, rather play the artist.
    # if something unknown and a known gerne/artist/song is given, ignore the unknown
    # if there is something unknown like 'very very hard rock' recursiveley remove the first? word and parse each argument
    response = Response() # errorCode.Success and suggestion = None
    arg_gernes = []
    for chunk in arguments:
        gerne = trimGerne(chunk)
        if isGerne(gerne) == True:
            arg_gernes.append(gerne)

    if len(arguments) == 0:
       playOrResume()
    elif len(arg_gernes) < len(arguments) and containsSongOrArtist(arguments):
       print(arguments)
       print(colored("RESULT: playSongArtist(" + ", ".join(arguments) + ")", color))
       songpos = mpdcontrol.match_in_database(arguments[0])
       mpdcontrol.play(songpos)
    elif len(arg_gernes) > 0:
       playGernes(arg_gernes)
    else:
        # no gerne song artist found, check for alternate suggestions
        response.errorCode = ErrorCodeEnum.ParsingError
        # TODO: suggest a song / gerne / artist depending
        response.suggestion = gernes[randint(0, len(gernes)-1)]

    return response

def isGerne(gerne):
    if trimGerne(gerne).lower() in gernes:
        return True;
    return False;

def trimGerne(gerne):
    # cut ' music' in the end
    music = "music"
    if gerne.lower().endswith(music):
        gerne = gerne[:len(gerne)-(len(music)+1)]
    return gerne

def playGernes(gernes):
    print(colored("RESULT: playGernes(" + ", ".join(gernes) + ")", color))

def containsSongOrArtist(arguments):
    for argument in arguments:
        if isArtist(argument) or isSong(argument):
            return True
    return False

def isArtist(argument):
    return argument.lower() in artists

def isSong(argument):
    return argument.lower() in songs

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