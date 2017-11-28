import http.client, urllib.parse, json
from xml.etree import ElementTree
from resources.supported_languages import TTSSupportedLocales, TTSLanguageCommand
import pyaudio
import wave

lang = TTSLanguageCommand()


class TextToSpeech:

    def __init__(self):

        try:
            with open('configs/configuration.json') as json_file:
                json_data = json.load(json_file)
                self.BING_KEY = json_data.get('Bing_Key')

            self.accesstoken = self.get_access_token()

        except FileNotFoundError as e:
            print(str(e))
        except KeyError as e:
            print(str(e) + " is not defined in config.json")

    def __del__(self):
        """


        """
        self.conn.close()

    def get_access_token(self):
        """

        :return:
        """

        headers = {"Ocp-Apim-Subscription-Key": self.BING_KEY}
        params = ""
        # AccessTokenUri = "https://api.cognitive.microsoft.com/sts/v1.0/issueToken";
        AccessTokenHost = "api.cognitive.microsoft.com"
        path = "/sts/v1.0/issueToken"

        # Connect to server to get the Access Token
        print("Connect to server to get the Access Token")
        conn = http.client.HTTPSConnection(AccessTokenHost)
        conn.request("POST", path, params, headers)
        response = conn.getresponse()
        if response.status == 200 and response.reason == 'OK':
            data = response.read()
            conn.close()
            accesstoken = data.decode("UTF-8")
        else:
            raise ValueError("Did not get the access token from microsoft bing")

        return accesstoken

    def request_to_bing(self, language='en-US', gender='Female', text=None, mode="riff-16khz-16bit-mono-pcm"):
        """

        :return:
        """

        body = ElementTree.Element('speak', version='1.0')
        body.set('{http://www.w3.org/XML/1998/namespace}lang', language)
        voice = ElementTree.SubElement(body, 'voice')
        voice.set('{http://www.w3.org/XML/1998/namespace}lang', language)
        voice.set('{http://www.w3.org/XML/1998/namespace}gender', gender)
        #voice.set('name', "Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)")
        service_name_map = lang(language, gender)
        voice.set('name', service_name_map)
        if text is None:
            #voice.text = 'This is a demo to call microsoft text to speech service in Python.'
            voice.text = 'now i will play music from david bowie'
        else:
            if isinstance(text, str):
                voice.text = text
            else:
                raise TypeError("text must be a string object")

        headers = {"Content-type": "application/ssml+xml",
                   "X-Microsoft-OutputFormat": mode,
                   #"X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                   "Authorization": "Bearer " + self.accesstoken,
                   "X-Search-AppId": "07D3234E49CE426DAA29772419F436CA",
                   "X-Search-ClientID": "1ECFAE91408841A480F00935DC390960",
                   "User-Agent": "TTSForPython"}

        # Connect to server to synthesize the wave
        print("\nConnect to server to get wav stream")
        self.conn = http.client.HTTPSConnection("speech.platform.bing.com")
        self.conn.request("POST", "/synthesize", ElementTree.tostring(body), headers)
        response = self.conn.getresponse()

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

if __name__ == '__main__':

    tts = TextToSpeech()
    resp = tts.request_to_bing(language='en-US', gender='Female', text='Play music from David Bowie')
    tts.play_request(resp)




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