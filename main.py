import json

from speech_to_text import SpeechToText
from text_to_speech  import TextToSpeech

try:
    with open('configs/configuration.json') as json_file:
        json_data = json.load(json_file)
    BING_KEY = json_data.get('Bing_Key')
except FileNotFoundError as e:
    print(str(e))
except KeyError as e:
    print(str(e) + " is not defined in config.json")


if __name__ == '__main__':

    sst = SpeechToText(Bing_Key=BING_KEY, mode='interactive_dictation', language='germany')
    sst_response = sst.start_recognize(recognizer='listen')
    tts = TextToSpeech()
    resp = tts.request_to_bing(language='de-DE', gender='Female', text=sst_response)
    tts.play_request(resp)