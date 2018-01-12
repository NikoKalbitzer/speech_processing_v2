import spacy
import MPD_NLP.service.mpd_provider_module as mpm
from MPD_NLP.service import verbalizer
from expiringdict import ExpiringDict
from random import randint
from MPD_NLP.service.conversationState import ConversationStateEnum, ConversationState
#from MPD_NLP.service.response import Response, ErrorCodeEnum
from flask import Flask, request
app = Flask(__name__)

nlp = spacy.load("en_core_web_lg")
#nlp = spacy.load("en")

# conversation state is stored in a expiringdict
# note that there an additional state which is also the initial state which is considered if no state is stored

states = ExpiringDict(max_len=100, max_age_seconds=10)
# states[userid] = ConversationState(ConversationStateEnum.AwaitYesOrNo, "Ask for David Bowie?")


print("READY for requests")

@app.route("/", methods=['POST'])
def parseREST():
    #input = request.args.get('input')
    #userid = request.args.get('userid')
    bytes_obj = request.get_data()
    resp_string = bytes_obj.decode('utf-8')
    print(resp_string)
    #print("REQUEST from id " + userid + ": " + input)
    userid= 1
    return parse(resp_string, userid)


def parse(input, userid):
    #start with part of speech tagging
    doc = nlp(input)

    response = "initial value aka no instruction found."

    try:
        if states.get(userid) == None:
            for token in doc:
                if token.lemma_ == "play":
                    print("PLAY instruction found")
                    # check if there is a negation
                    if is_negative(token) != True:
                        if token.nbor().lemma_ == "next":
                            response = playNext()
                        elif len(doc) > 1 and token.nbor().lemma_ == "previous":
                            response = playPrevious()
                        elif len(doc) > 1 and token.nbor().lemma_ == "random":
                            response = playRandom()
                        elif len(doc) > 2 and token.nbor().lemma_ == "a" and token.nbor().nbor().lemma_ == "random":
                            response = playRandom()
                        elif len(doc) > 1 and token.nbor().lemma_ == "something":
                            # ask for a artist/songname or gerne
                            states[userid] = ConversationState(ConversationStateEnum.AwaitSongArtistOrGerne)
                            response = verbalizer.getQuestionForArtistSongGerneOrRandom()
                            mpm.speak(response)
                        else:
                            response = play(doc, userid)
                    else:
                        # input is something like: Don't play David Bowie.
                        response = verbalizer.getDontPlayText()
                        mpm.speak(response)
                    break
                elif token.lemma_ == "stop":
                    print("STOP instruction found")
                    if is_negative(token) != True:
                        response = stop()
                    else:
                        # input is something like: Don't stop.
                        response = verbalizer.getDontStopPauseText()
                        mpm.speak(response)
                    break
                elif token.lemma_ == "pause":
                    print("PAUSE instruction found")
                    if is_negative(token) != True:
                        response = pause()
                    else:
                        # input is something like: Don't pause.
                        response = verbalizer.getDontStopPauseText()
                        mpm.speak(response)
                    break
                elif token.lemma_ == "resume" or token.lemma_ == "continue":
                    print("RESUME instruction found")
                    if is_negative(token) != True:
                        response = resume()
                    else:
                        # input is something like: Don't resume.
                        response = verbalizer.getDontResumeText()
                        mpm.speak(response)
                    break
                elif token.lemma_ == "next" and len(doc) <= 3:
                    print("NEXT instruction found")
                    response = playNext()
                    break
                elif token.lemma_ == "previous" and len(doc) <= 3:
                    print("PREVIOUS instruction found")
                    response = playPrevious()
                    break
                elif token.lemma_ == "clear":
                    print("CLEAR instruction found")
                    if is_negative(token) != True and 'playlist' in (str(word).lower() for word in doc):
                        response = clearCurrentPlaylist()
                    break
                elif token.lemma_ == "update":
                    print("UPDATE instruction found")
                    if is_negative(token) != True and 'database' in (str(word).lower() for word in doc):
                        response = updateDatabase()
                    break
                elif token.lemma_ == "repeat":
                    print("REPEAT instruction found")
                    if is_negative(token) != True:
                        if 'playlist' in (str(word).lower() for word in doc):
                            response = repeatPlaylist()
                        elif 'song' in (str(word).lower() for word in doc):
                            response = repeatSong()
                    break

        elif states.get(userid).state == ConversationStateEnum.AwaitYesOrNo:
            print("Yes or no")
            state = states.pop(userid) # remove state
            if doc[0].lemma_ == "yes":
                response = parse(state.suggestion, userid) # simply call with a suggestion like 'Play rock.'
            else:
                response = "Oh, ok."

            mpm.speak(response)
        elif states.get(userid).state == ConversationStateEnum.AwaitSongArtistOrGerne:
            print("Song, Gerne or Artist")
            states.pop(userid) # remove state
            return parse("Play " + str(doc), userid)
    except Exception as e: # specify Exception
        response = verbalizer.getConnectionError()
        mpm.speak(response)
        raise e

    return ">>" + response + "\n"


def is_negative(token):
    # if there is a negation for play, it is a children of play in the graph
    for child in token.children:
        #print(child.text + " " + child.dep_)
        if child.dep_ == "neg":
            print("NEG found")
            return True
    return False


def play(doc, userid):
    chunks = list(doc.noun_chunks)
    # determine if this chunks are gernes, artists or songs
    # for gerne:
    # should be only one chunk with one word or <GERNE> + music
    print("CHUNKS: " + str(chunks))

    arguments = []
    for chunk in chunks:
        arguments.append(str(chunk))

    response = verbalizer.getOkText()

    arg_gernes = []
    for chunk in arguments:
        gerne = mpm.trimGerne(chunk)
        if mpm.isGerne(gerne) == True:
            arg_gernes.append(gerne)

    print(arg_gernes)

    if len(arguments) == 0:
        mpm.speak(response)
        mpm.playOrResume()
    elif len(arg_gernes) < len(arguments) and mpm.containsSongOrArtist(arguments):
        mpm.speak(response)
        mpm.playSongOrArtist(arguments)
    elif len(arg_gernes) > 0:
        mpm.speak(response)
        mpm.playGernes(arg_gernes)
    else:
        # no gerne song artist found, check for alternate suggestions
        # TODO: suggest a song / gerne / artist depending
        suggestion = mpm.getRandomGenre()
        states[userid] = ConversationState(ConversationStateEnum.AwaitYesOrNo, "Play " + suggestion + ".")
        response = verbalizer.getAlternatePlaySuggestion(suggestion)
    return response

def stop():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.stop()  # TODO: check response
    return response

def pause():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.pause() # TODO: check response
    return response

def resume():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.resume() # TODO: check response
    return response

def playNext():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.playNext() # TODO: check response
    return response

def playPrevious():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.playPrevious() # TODO: check response
    return response

def playRandom():
    mpm.playRandom() # TODO: check response
    return verbalizer.getOkText()

def clearCurrentPlaylist():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.clearCurrentPlaylist() # TODO: check response
    return response

def updateDatabase():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.updateDatabase() # TODO: check response
    return response

def repeatSong():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.repeatSong() # TODO: check response
    return response

def repeatPlaylist():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.repeatPlaylist() # TODO: check response
    return response

if __name__ == '__main__':
    #resp = parse("play Alan Walker", 1)
    #print(resp)
    app.run(debug=True)