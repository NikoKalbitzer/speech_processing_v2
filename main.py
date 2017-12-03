import json
from speech_control.speech_to_text import SpeechToText
from speech_control.text_to_speech  import TextToSpeech


if __name__ == '__main__':

    try:

        with open('configs/configuration.json') as json_file:
            json_data = json.load(json_file)

        BING_KEY = json_data.get('Bing_Key')

        stt = SpeechToText(bing_key=BING_KEY, mode='interactive', language='germany')
        stt_response = stt.start_recognize(recognizer='listen')

        tts = TextToSpeech(bing_key=BING_KEY, language='germany', gender='Female')
        if 'DisplayText' in stt_response:
            resp = tts.request_to_bing(text=stt_response['DisplayText'])
            tts.play_request(resp)
        else:
            print("no DisplayText available")

    except FileNotFoundError as e:
        print(str(e))
    except KeyError as e:
        print(str(e) + " is not defined in config.json")