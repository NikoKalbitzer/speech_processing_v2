import json
import requests
from termcolor import colored
from speech_control.speech_to_text import SpeechToText
from speech_control.text_to_speech import TextToSpeech
# EXCEPTIONS
from audio.recognizer import RequestError, UnknownValueError
from requests.packages.urllib3.exceptions import NewConnectionError, MaxRetryError
from requests.exceptions import ConnectionError


def main():
    try:
        with open('configs/configuration.json') as json_file:
            json_data = json.load(json_file)

        if json_data['speech_engine'] == "google":
            flask_server = json_data['flask']['server']

            stt = SpeechToText(mode='interactive', language='united_states')
            stt_resp = stt.start_recognize(speech_engine="google", recognizer='listen')
            print("You said: " + colored(stt_resp, "green"))
            requests.post(url=flask_server, data=stt_resp)

        else:

            BING_KEY = json_data['bing']['bing_key']

            flask_server = json_data['flask']['server']

            stt = SpeechToText(bing_key=BING_KEY, mode='interactive', language='united_states')
            stt_resp = stt.start_recognize(speech_engine="bing", recognizer='listen')
            print(stt_resp)
            if 'DisplayText' in stt_resp:
                print(stt_resp['DisplayText'])
                #send stt response to parse_server
                requests.post(url=flask_server, data=stt_resp['DisplayText'])

            else:
                print("Did not understand, please retry")

    except RequestError:
        print(colored("RequestError: please check your api key for validity!", "red"))

    except UnknownValueError:
        print(colored("UnknownValueError: you have to say something! ", "red"))

    except (ConnectionRefusedError, NewConnectionError, MaxRetryError, ConnectionError):
        print(colored("ConnectionError: check if your FLASK server is running!", "red"))

    except OSError:
        print(colored("OSError: check if you plugged in a microphone!", "red"))


if __name__ == '__main__':
    main()


