import spacy
from termcolor import colored
import MPD_NLP.service.mpd_provider_module as mpm
from MPD_NLP.service import verbalizer
from enum import Enum
from expiringdict import ExpiringDict
from MPD_NLP.service.conversationState import ConversationStateEnum, ConversationState
from MPD_NLP.service.response import Response, ErrorCodeEnum
from flask import Flask, request
app = Flask(__name__)

nlp = spacy.load("en_core_web_lg")


# conversation state is stored in a expiringdict
# note that there an additional state which is also the initial state which is considered if no state is stored

states = ExpiringDict(max_len=100, max_age_seconds=10)
# states[userid] = ConversationState(ConversationStateEnum.AwaitYesOrNo, "Ask for David Bowie?")


print("READY for requests")



@app.route("/")
def parseREST():
    input = request.args.get('input')
    userid = request.args.get('userid')
    print("REQUEST from id " + userid + ": " + input)
    return parse(input, userid)


def parse(input, userid):
    #start with part of speech tagging
    doc = nlp(input)
    print(doc)
    response = "initial value aka no instruction found."

    if states.get(userid) == None:
        for token in doc:
            if token.lemma_ == "play":

                print("PLAY instruction found")
                # check if there is a negation
                if is_negative(token) != True:
                    if token.nbor().lemma_ == "next":
                        response = playNext()
                    elif token.nbor().lemma_ == "random":
                        response = playRandom()
                    elif token.nbor().lemma_ == "a" and token.nbor().nbor().lemma == "random":
                        response = playRandom()
                    elif token.nbor().lemma_ == "something":
                        # ask for a artist/songname or gerne
                        states[userid] = ConversationState(ConversationStateEnum.AwaitSongArtistOrGerne)
                        return verbalizer.getQuestionForArtistSongGerneOrRandom()
                    else:
                        response = play(doc, userid)
                else:
                    # input is something like: Don't play David Bowie.
                    response = verbalizer.getDontPlayText()
                break
            elif token.lemma_ == "stop":
                print("STOP instruction found")
                if is_negative(token) != True:
                    response = stop()
                else:
                    # input is something like: Don't stop.
                    response = verbalizer.getDontStopPauseText()
                break
            elif token.lemma_ == "pause":
                print("PAUSE instruction found")
                if is_negative(token) != True:
                    response = pause()
                else:
                    # input is something like: Don't pause.
                    response = verbalizer.getDontStopPauseText()
                break
            elif token.lemma_ == "resume" or token.lemma_ == "continue":
                print("RESUME instruction found")
                if is_negative(token) != True:
                    response = resume()
                else:
                    # input is something like: Don't resume.
                    response = verbalizer.getDontResumeText()
                break
            elif token.lemma_ == "next" and len(doc) <= 2:
                print("NEXT instruction found")
                response = playNext()
                break

    elif states.get(userid).state == ConversationStateEnum.AwaitYesOrNo:
        print("Yes or no")
        state = states.pop(userid) # remove state
        if doc[0].lemma_ == "yes":
            return parse(state.suggestion, userid) # simply call with a suggestion like 'Play rock.'
        else:
            return "Oh, ok."
    elif states.get(userid).state == ConversationStateEnum.AwaitSongArtistOrGerne:
        print("Song, Gerne or Artist")
        states.pop(userid) # remove state
        return parse("Play " + str(doc), userid)

    return ">> " + response + "\n"

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

    response = mpm.playGerneSongArtist(arguments)

    if response.errorCode == ErrorCodeEnum.Success:
        return verbalizer.getOkText()
    elif response.errorCode == ErrorCodeEnum.ParsingError:
        states[userid] = ConversationState(ConversationStateEnum.AwaitYesOrNo, "Play " + response.suggestion + ".")
        return verbalizer.getAlternatePlaySuggestion(response.suggestion)
    elif response.errorCode == ErrorCodeEnum.ConnectionError:
        return verbalizer.getConnectionError()

def stop():
    mpm.stop()
    return verbalizer.getOkText()

def pause():
    mpm.pause()
    return verbalizer.getOkText()

def resume():
    mpm.resume()
    return verbalizer.getOkText()

def playNext():
    mpm.playNext()
    return verbalizer.getOkText()

def playRandom():
    mpm.playRandom()
    return verbalizer.getOkText()


if __name__ == '__main__':
    resp = parse("stop the current song", 1)
    #print(resp)