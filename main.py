import json
from speech_control.speech_to_text import SpeechToText
from speech_control.text_to_speech import TextToSpeech

if __name__ == '__main__':

    try:

        with open('configs/configuration.json') as json_file:
            json_data = json.load(json_file)

        BING_KEY = json_data.get('Bing_Key')

        stt = SpeechToText(bing_key=BING_KEY, mode='interactive', language='united_states')
        #mpdclient = ControlMPD(json_data.get('MPD_Server'), json_data.get('MPD_Port'))


        stt_response = stt.start_recognize(recognizer='listen_in_background')
        #str_for_mpd = stt_response['DisplayText'].strip(".").split(" ")
        #print(str_for_mpd)
        #mpdclient.clear_current_playlist()
        #print(mpdclient.get_current_song_playlist())
        #mpdclient.update_database()
        """
        try:
            songpos = mpdclient.match_in_database(str_for_mpd[1])
            print(songpos)
            mpdclient.play(songpos)
            sleep(10)
            mpdclient.stop()
        except (IndexError, CommandError):
            tts = TextToSpeech(bing_key=BING_KEY, language='united_states', gender='Female')
            resp = tts.request_to_bing(text='Sry i did not understand!')
            tts.play_request(resp)
        """
    except FileNotFoundError as e:
        print(str(e))
    except KeyError as e:
        print(str(e) + " is not defined in config.json")
