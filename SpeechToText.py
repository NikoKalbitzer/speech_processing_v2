import json
from os import path
from Audio.AudioFile import AudioFile
from Recognizer import Recognizer, UnknownValueError, RequestError
from Microphone import Microphone
from resources.supported_languages import interactive_dictation, conversation

try:
    with open('configs/configuration.json') as json_file:
        json_data = json.load(json_file)
except FileNotFoundError as e:
    print(str(e))
except KeyError as e:
    print(str(e) + " is not defined in config.json")


def speech_to_text(language='germany', mode=None, recognizer='listen', duration=5):

    BING_KEY = json_data.get('Bing_Key')  # Microsoft Bing Voice Recognition API keys 32-character lowercase
                                          #  hexadecimal strings
    language = interactive_dictation[language]

    rec = Recognizer()

    if recognizer is 'listen':
        with Microphone() as source:
            print("Please say something: ...")
            audio = rec.listen(source)

    elif recognizer is 'recorder':
        if isinstance(duration, int):
            with Microphone() as source:
                print("Please say something: ...")
                audio = rec.record(source, duration=duration)
        else:
            raise TypeError("duration must be an integer")
    else:
        AUDIO_FILE = path.join('resources/wav_files/please_tell_me_the_weather.wav')

        with AudioFile(AUDIO_FILE) as source:
            audio = rec.record(source)  # read the entire audio file

    print("Recording finished!")

    result = rec.recognize_bing(audio, key=BING_KEY, language=language, show_all=True)
    print(result)
    if 'DisplayText' in result:
        try:
            print("You said: " + result['DisplayText'])
        except UnknownValueError:
            print("Bing Voice Recognition could not understand audio")
        except RequestError as e:
            print("Could not request results from Bing Voice Recognition service; {0}".format(e))


def record_to_wav():
    import pyaudio
    import wave

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "output.wav"

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

if __name__ == "__main__":
    speech_to_text()
