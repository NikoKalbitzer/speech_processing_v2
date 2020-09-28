import spacy
import string
import nlp.service.mpd_provider_module as mpm
import logging as log
from nlp.service import verbalizer
from expiringdict import ExpiringDict
from nlp.service.conversationState import ConversationStateEnum, ConversationState
from flask import Flask, request
from SpotifyRecommender import recommender, tag_extractor

app = Flask(__name__)

nlp = spacy.load("en_core_web_lg")
# nlp = spacy.load("en")
recommender_inst = None

# conversation state is stored in a expiringdict
# note that there an additional state which is also the initial state which is considered if no state is stored

states = ExpiringDict(max_len=100, max_age_seconds=10)

verbose = True

if verbose:
    log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
    log.info("Verbose output.")
else:
    log.basicConfig(format="%(levelname)s: %(message)s")

print("READY for requests")


@app.route("/", methods=['POST'])
def parseREST():
    # input = request.args.get('input')
    # userid = request.args.get('userid')
    bytes_obj = request.get_data()
    resp_string = bytes_obj.decode('utf-8')
    print(resp_string)
    # print("REQUEST from id " + userid + ": " + input)
    userid = 1
    return parse(resp_string, userid)


def parse(input, userid):
    # start with part of speech tagging
    doc = nlp(input)

    response = ""

    try:
        if states.get(userid) == None:
            for token in doc:
                if token.lemma_ == "play":
                    log.info("PLAY instruction found")
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
                            response
                        else:
                            response = play(doc, userid)
                    else:
                        # input is something like: Don't play David Bowie.
                        response = verbalizer.getDontPlayText()
                        mpm.speak(response)
                    break
                elif token.lemma_ == "stop":
                    log.info("STOP instruction found")
                    if is_negative(token) != True:
                        response = stop()
                    else:
                        # input is something like: Don't stop.
                        response = verbalizer.getDontStopPauseText()
                        mpm.speak(response)
                    break
                elif token.lemma_ == "pause":
                    log.info("PAUSE instruction found")
                    if is_negative(token) != True:
                        response = pause()
                    else:
                        # input is something like: Don't pause.
                        response = verbalizer.getDontStopPauseText()
                        mpm.speak(response)
                    break
                elif token.lemma_ == "resume" or token.lemma_ == "continue":
                    log.info("RESUME instruction found")
                    if is_negative(token) != True:
                        response = resume()
                    else:
                        # input is something like: Don't resume.
                        response = verbalizer.getDontResumeText()
                        mpm.speak(response)
                    break
                elif token.lemma_ == "next" and len(doc) <= 3:
                    log.info("NEXT instruction found")
                    response = playNext()
                    break
                elif token.lemma_ == "previous" and len(doc) <= 3:
                    log.info("PREVIOUS instruction found")
                    response = playPrevious()
                    break
                elif token.lemma_ == "clear":
                    log.info("CLEAR instruction found")
                    if is_negative(token) != True and 'playlist' in (str(word).lower() for word in doc):
                        response = clearCurrentPlaylist()
                    break
                elif token.lemma_ == "update":
                    log.info("UPDATE instruction found")
                    if is_negative(token) != True and 'database' in (str(word).lower() for word in doc):
                        response = updateDatabase()
                    break
                elif token.lemma_ == "repeat":
                    log.info("REPEAT instruction found")
                    if is_negative(token) != True:
                        if 'playlist' in (str(word).lower() for word in doc):
                            response = repeatPlaylist()
                        elif 'song' in (str(word).lower() for word in doc):
                            response = repeatSong()
                    break
                elif token.lemma_ == "recommend":
                    if not is_negative(token):
                        if len(doc) == 3 and token.nbor().lemma_ == "a" and token.nbor().nbor().lemma_ == "song":
                            recommender_inst.recommend_song()
                            response = "recommending song"
                        elif len(
                                doc) > 3 and token.nbor().lemma_ == "a" and token.nbor().nbor().nbor().lemma_ == "song":
                            recommender_inst.recommend_genre_or_mood(token.nbor().nbor().lemma_)
                            response = "recommend a song with parameter:" + token.nbor().nbor().lemma_
                        elif len(doc) == 2 and token.nbor().lemma_ == "playlist":
                            recommender_inst.recommend_list_of_songs()
                            response = "Playing list of your most recommended songs!"
                elif token.lemma_ == "initialize":
                    if not is_negative(token):
                        if len(doc) == 2 and token.nbor().lemma_ == "recommend":
                            response = "Initializing the recommender. This may take a while."
                            tag_extractor.TagExtractor()
                            global recommender_inst
                            recommender_inst = recommender.Recommender()
        elif states.get(userid).state == ConversationStateEnum.AwaitYesOrNo:
            log.info("Yes or no")
            state = states.pop(userid)  # remove state
            if doc[0].lemma_ == "yes":
                response = parse(state.suggestion, userid)  # simply call with a suggestion like 'Play rock.'
            else:
                response = "Oh, ok."

            mpm.speak(response)
        elif states.get(userid).state == ConversationStateEnum.AwaitSongArtistOrGerne:
            log.info("Song, Genre or Artist")
            states.pop(userid)  # remove state
            return parse("Play " + str(doc), userid)
    except Exception as e:  # specify Exception
        response = verbalizer.getConnectionError()
        mpm.speak(response)
        raise e

    # no keyword was found
    if response == "":
        suggestion = mpm.getRandomGenre()
        states[userid] = ConversationState(ConversationStateEnum.AwaitYesOrNo, "Play " + suggestion + ".")
        response = verbalizer.getAlternatePlaySuggestion(suggestion)
        mpm.speak(response)

    return response


def is_negative(token):
    # if there is a negation for play, it is a children of play in the graph
    for child in token.children:
        # print(child.text + " " + child.dep_)
        if child.dep_ == "neg":
            log.info("NEG found")
            return True
    return False


def play(doc, userid):
    chunks = list(doc.noun_chunks)
    # determine if this chunks are gernes, artists or songs
    # for gerne:
    # should be only one chunk with one word or <GERNE> + music
    log.info("CHUNKS: " + str(chunks))

    arguments = []
    for chunk in chunks:
        arguments.append(str(chunk))

    # in some cases chunk analysis takes play within the chunk
    if len(arguments) > 0 and arguments[0].lower().startswith("play") and doc.text.lower().count("play") == arguments[
        0].lower().count("play"):
        arguments[0] = arguments[0][5:]
        if "" in arguments:
            arguments.remove("")

    # if chunk analysis fails, set chunk manually (this happens in short instructions)
    if len(arguments) == 0:
        table = str.maketrans({key: None for key in string.punctuation})
        arguments.append(doc.text[5:].translate(table))
        if "" in arguments:
            arguments.remove("")

    response = verbalizer.getOkText()

    arg_genres = []
    for chunk in arguments:
        genre = mpm.trimGerne(chunk)
        if mpm.isGerne(genre) == True:
            arg_genres.append(genre)

    log.info(arg_genres)
    if len(arguments) == 0:
        mpm.speak(response)
        mpm.playOrResume()
    elif len(arg_genres) < len(arguments) and mpm.containsSongOrArtist(arguments):
        mpm.speak(response)
        mpm.playSongOrArtist(arguments)
    elif len(arg_genres) > 0:
        mpm.speak(response)
        mpm.playGernes(arg_genres)
    else:
        # no genre song artist found, check for alternate suggestions
        suggestion = mpm.getRandomGenre()
        states[userid] = ConversationState(ConversationStateEnum.AwaitYesOrNo, "Play " + suggestion + ".")
        response = verbalizer.getAlternatePlaySuggestion(suggestion)
    return response


def stop():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.stop()
    return response


def pause():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.pause()
    return response


def resume():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.resume()
    return response


def playNext():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.playNext()
    return response


def playPrevious():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.playPrevious()
    return response


def playRandom():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.playRandom()
    return verbalizer.getOkText()


def clearCurrentPlaylist():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.clearCurrentPlaylist()
    return response


def updateDatabase():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.updateDatabase()
    return response


def repeatSong():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.repeatSong()
    return response


def repeatPlaylist():
    response = verbalizer.getOkText()
    mpm.speak(response)
    mpm.repeatPlaylist()
    return response


if __name__ == '__main__':
    app.run(debug=True)
