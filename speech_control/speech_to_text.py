import pyaudio
import wave
from os import path
from audio.audio_file import AudioFile
from audio.recognizer import Recognizer, UnknownValueError, RequestError
from audio.microphone import Microphone
from resources.supported_languages import STTLanguageCommand
from music_player.mpd_connection import ControlMPD
import time
from MPD_NLP.service.parse import *

class SpeechToText:

    def __init__(self, bing_key, mode=None, language=None):
        """
        constructor to initialize bing_key, mode settings and appropiate language

        :param bing_key: string, bing api key to get the access token
        :param mode: string, select mode: interactive(default), dictation, conversation
        :param language: string, 'germany' is default string value
        """

        if isinstance(bing_key, str):
            self.bing_key = bing_key
        else:
            raise TypeError("'bing_key' must be type of string")

        if mode is None:
            self.mode = 'interactive'
        else:
            if isinstance(mode, str):
                if (mode == 'interactive') or (mode == 'dictation') or (mode == 'conversation'):
                    self.mode = mode
                else:
                    raise UnknownValueError("'mode' must be 'interactive', 'dictation' or 'conversation'")
            else:
                raise TypeError("'mode' must be type of string")

        if language is None:
            self.language = 'germany'
        else:
            if isinstance(language, str):
                self.language = language
            else:
                raise TypeError("'language' must be type of string")

        self.stt_lang = STTLanguageCommand()
        self.language_abbreviation = self.stt_lang(self.mode, self.language)

        self.recognizer = Recognizer()
        #self.mpdclient = ControlMPD('192.168.178.37', 6600)

    def set_language(self, language):
        """
        method to set another language
        """

        if isinstance(language, str):
            self.language = language
            self.language_abbreviation = self.stt_lang(self.mode, language)
        else:
            raise TypeError("'mode' and 'language' must be type of string")

    def get_language(self):
        """
        method to get the language and the abbreviation of selected language
        :return: string
        """
        return "language: {}, language_abbreviation: {}".format(self.language, self.language_abbreviation)

    def set_mode(self, mode):
        """

        :return:
        """
        if isinstance(mode, str):
            if (mode == 'interactive') or (mode == 'dictation') or (mode == 'conversation'):
                self.mode = mode
            else:
                raise UnknownValueError("'mode' must be 'interactive', 'dictation' or 'conversation'")

        # TODO check language with selected mode , method: check_language_in_mode

    def get_mode(self):
        """
        method to get the current mode
        :return:
        """
        return self.mode

    def start_recognize(self, recognizer='listen', duration=None, path_to_audio=None):
        """
        method to start the recognizing dependent from the selected 'recognizer'

        :param recognizer: string, can be 'listen', 'recorder' or 'audio'
        :param duration: integer, in recognizer mode 'recorder', specify the duration of recording in seconds
        :param path_to_audio: string, path to the audio file

        :return: string, if the query was successfully, the appropriate display text will be appear
        """

        if recognizer is 'listen':
            with Microphone() as source:
                print("Please say something: ...")
                audio = self.recognizer.listen(source)

        elif recognizer is 'recorder':
            if duration is None:
                self.duration = 5
            else:
                if isinstance(duration, int):
                    self.duration = duration
                else:
                    raise TypeError("'duration' must be type of integer")

            with Microphone() as source:
                print("Please say something: ...")
                audio = self.recognizer.record(source, duration=self.duration)

        elif recognizer is 'audio':
            if path_to_audio is None:
                raise ValueError("please enter an audio path!")
            if isinstance(path_to_audio, str):
                audio_file = path.join(path_to_audio)
            else:
                raise TypeError("'path_to_audio' must be type of string")

            with AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)  # read the entire audio file

        elif recognizer is 'listen_in_background':
            with Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
            print("Please say something: ...")
            stop_listening = self.recognizer.listen_in_background(source, callback=self.get_result)
            print(stop_listening)
            #stop_listening()
            while True:
                time.sleep(0.1)

        else:
            return None

        print("Recording finished!")

        return self.get_result(audio)

    def get_result(self, audio):
        """
        method to get the result of the query as a dictionary

        :param audio, an AudioData instance

        :return: result, dict
        {'RecognitionStatus': 'InitialSilenceTimeout', 'Duration': 0, 'Offset': 13100000},
        {'DisplayText': 'Wie ist das Wetter heute?', 'Duration': 17700000, 'RecognitionStatus': 'Success', 'Offset': 4300000}
        """

        result = self.recognizer.recognize_bing(audio, key=self.bing_key, language=self.language_abbreviation, show_all=True)

        if 'DisplayText' in result:
            try:
                print("You said: " + result['DisplayText'])
                nlp_resp = parse(result['DisplayText'], 1)
                print(nlp_resp)
            except UnknownValueError:
                print("Bing Voice Recognition could not understand audio")
            except RequestError as e:
                print("Could not request results from Bing Voice Recognition service; {0}".format(e))

        else:
            return result

    def record_to_wav(self, output_file=None, record_duration=5):
        """
        method to save a recording as wav file

        :param output_file: string name to save the output file, default is "output.wav"
        :param record_duration: integer for the duration of recording in seconds, default is 5 seconds
        """

        if output_file is None:
            wave_output_filename = "output.wav"
        else:
            if isinstance(output_file, str):
                wave_output_filename = output_file
            else:
                raise TypeError("'output_file' must be type of string")

        if isinstance(record_duration, int):
            record_seconds = record_duration
        else:
            raise TypeError("record_duration must be type of integer")

        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 2
        RATE = 44100

        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        print("recording to wav file starts: ...")

        frames = []

        for i in range(0, int(RATE / CHUNK * record_seconds)):
            data = stream.read(CHUNK)
            frames.append(data)

        print("done recording")

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(wave_output_filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()


