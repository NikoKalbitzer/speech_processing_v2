import http.client, urllib.parse
from xml.etree import ElementTree
from resources.supported_languages import TTSLanguageCommand
import pyaudio



class TextToSpeech:

    def __init__(self, bing_key, language=None, gender=None, output_mode="riff-16khz-16bit-mono-pcm"):
        """
        constructor to initialize bing_key, language, gender and output mode

        :param bing_key: string, bing api key to get the access token
        :param language: string, select appropriate language for the output speech
        :param gender: string, gender of the speaker, can be 'Female' or 'Male'
        :param output_mode: string,
        """

        if isinstance(bing_key, str):
            self.bing_key = bing_key
        else:
            raise TypeError("'bing_key' must be type of string")

        self.access_token = self.__get_access_token()

        if language is None:
            self.language = 'germany'
        else:
            if isinstance(language, str):
                self.language = language
            else:
                raise TypeError("'language' must be type of string")

        if gender is None:
            self.gender = 'Female'
        else:
            if isinstance(gender, str):
                if (gender == 'Female') or (gender == 'Male'):
                    self.gender = gender
                else:
                    raise ValueError("'gender' must be 'Female' or 'Male'")
            else:
                raise TypeError("'gender' must be type of string")

        self.tts_lang = TTSLanguageCommand()

        self.language_abbreviation, self.service_name_map = self.tts_lang(self.language, self.gender)

        self.output_mode = output_mode

    def __get_access_token(self):
        """
        method to get the access token from Microsoft

        :return: access_token
        """

        headers = {"Ocp-Apim-Subscription-Key": self.bing_key}
        params = ""
        # AccessTokenUri = "https://api.cognitive.microsoft.com/sts/v1.0/issueToken";
        access_token_host = "api.cognitive.microsoft.com"
        path = "/sts/v1.0/issueToken"

        # Connect to server to get the Access Token
        conn = http.client.HTTPSConnection(access_token_host)
        conn.request("POST", path, params, headers)
        response = conn.getresponse()
        if response.status == 200 and response.reason == 'OK':
            data = response.read()
            conn.close()
            access_token = data.decode("UTF-8")
            return access_token
        else:
            raise ValueError("Did not get the access token from microsoft bing")

    def request_to_bing(self, text=None):
        """
        method to request the Microsoft text to speech service

        :param text, string, given text to speak
        :return:
        """

        body = ElementTree.Element('speak', version='1.0')
        body.set('{http://www.w3.org/XML/1998/namespace}lang', self.language_abbreviation)
        voice = ElementTree.SubElement(body, 'voice')
        voice.set('{http://www.w3.org/XML/1998/namespace}lang', self.language_abbreviation)
        voice.set('{http://www.w3.org/XML/1998/namespace}gender', self.gender)
        voice.set('name', self.service_name_map)
        if text is None:
            voice.text = 'This is a demo to call microsoft text to speech service in Python.'
        else:
            if isinstance(text, str):
                voice.text = text
            else:
                raise TypeError("text must be a type of string")

        headers = {"Content-type": "application/ssml+xml",
                   "X-Microsoft-OutputFormat": self.output_mode,
                   "Authorization": "Bearer " + self.access_token,
                   "X-Search-AppId": "07D3234E49CE426DAA29772419F436CA",
                   "X-Search-ClientID": "1ECFAE91408841A480F00935DC390960",
                   "User-Agent": "TTSForPython"}

        # Connect to server to synthesize the wave
        print("\nConnect to server to get wav stream")
        conn = http.client.HTTPSConnection("speech.platform.bing.com")
        conn.request("POST", "/synthesize", ElementTree.tostring(body), headers)
        response = conn.getresponse()

        if response.status == 200 and response.reason == 'OK':
            return response
        else:
            raise ValueError("Did not get a correct response from microsoft server")

    def play_request(self, http_response):
        """

        :return:
        """
        CHUNK = 1024
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(2),
                        channels=1,
                        rate=16000,
                        output=True)

        if isinstance(http_response, http.client.HTTPResponse):
            data = http_response.read(CHUNK)

            # play stream
            while len(data) > 0:
                stream.write(data)
                data = http_response.read(CHUNK)

            # stop stream
            stream.stop_stream()
            stream.close()

            # close PyAudio
            p.terminate()
        else:
            raise TypeError("http_response must be a HTTPResponse object")


#data = response.read()
#wf = wave.open("file.wav", 'wb')
#wf.setnchannels(1)
#wf.setsampwidth(2)
#wf.setframerate(16000)
#wf.writeframesraw(data)
#wf.close()
#with open("file.wav", "w") as f:
#    f.write(data)
#print(type(data))
#print(len(data))



#wf = wave.open('file.wav', 'rb')



# instantiate PyAudio (1)


# open stream (2)
#stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
 #               channels=wf.getnchannels(),
  #              rate=wf.getframerate(),
   #             output=True)

#("The synthesized wave length: %d" % (len(data)))