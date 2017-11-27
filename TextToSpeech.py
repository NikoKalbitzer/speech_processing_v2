import http.client, urllib.parse, json
from xml.etree import ElementTree
import pyaudio
import wave

apiKey = "57f24776951f4c1ea98c074099bcf614"

params = ""
headers = {"Ocp-Apim-Subscription-Key": apiKey}

# AccessTokenUri = "https://api.cognitive.microsoft.com/sts/v1.0/issueToken";
AccessTokenHost = "api.cognitive.microsoft.com"
path = "/sts/v1.0/issueToken"

# Connect to server to get the Access Token
print("Connect to server to get the Access Token")
conn = http.client.HTTPSConnection(AccessTokenHost)
conn.request("POST", path, params, headers)
response = conn.getresponse()
print(response.status, response.reason)

data = response.read()
conn.close()

accesstoken = data.decode("UTF-8")
print("Access Token: " + accesstoken)

body = ElementTree.Element('speak', version='1.0')
body.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-us')
voice = ElementTree.SubElement(body, 'voice')
voice.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-US')
voice.set('{http://www.w3.org/XML/1998/namespace}gender', 'Female')
voice.set('name', 'Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)')
voice.text = 'This is a demo to call microsoft text to speech service in Python.'

headers = {"Content-type": "application/ssml+xml",
           "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
           #"X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
           "Authorization": "Bearer " + accesstoken,
           "X-Search-AppId": "07D3234E49CE426DAA29772419F436CA",
           "X-Search-ClientID": "1ECFAE91408841A480F00935DC390960",
           "User-Agent": "TTSForPython"}

# Connect to server to synthesize the wave
print("\nConnect to server to synthesize the wave")
conn = http.client.HTTPSConnection("speech.platform.bing.com")
conn.request("POST", "/synthesize", ElementTree.tostring(body), headers)
response = conn.getresponse()
print(response.status, response.reason)

data = response.read()

with open("file.wav", "w") as f:
    f.write(b''.join(data))
#print(type(data))
#print(len(data))
"""
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

p = pyaudio.PyAudio()

#stream = p.open(format=FORMAT,
#                channels=CHANNELS,
#                rate=RATE,
#                input=True,
#                frames_per_buffer=CHUNK)

#print("* recording")

#frames = []

#for i in range(0, len(data)):
#    data = stream.read(CHUNK)
#    frames.append(data)

#print("* done recording")

#stream.stop_stream()
#stream.close()
#p.terminate()

wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(16000)
while True:
    da = response.read(1024)
    if not da:
        break
    #wf.writeframes(b''.join(frames))
    wf.writeframes(da)
wf.close()
"""


conn.close()
print("The synthesized wave length: %d" % (len(data)))