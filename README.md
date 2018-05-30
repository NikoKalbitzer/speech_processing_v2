# Speech processing

This Repository was created for a project @ [Ostbayerische Technische Hochschule Regensburg](https://www.oth-regensburg.de/) in WS 17/18

<br>
In the current state, following actions are possible:
<br>

- Speech to text conversion with google´s or microsoft´s speech api
- Natural language processing with [spacy](https://spacy.io/)
- Speech control of the [MPD](https://www.musicpd.org/)
- Speech recognition with audio files

## Prerequisites
#### Python version 3.5
Please ensure, that you use python 3.5. Check before you start:

Terminal on windows:
<pre><code>
py -3.5
</pre></code>
Terminal on Linux:
<pre><code>
python3
</pre></code>

#### File "configuration.json" in folder configs
If you have other settings for mpd, flask than the default file, please change it to
your preference
<pre><code>
{
  "speech_engine": "google",
  "mpd": {
    "server": "localhost",
    "port": 6600
  },
  "flask": {
    "server": "http://127.0.0.1:5000"
  },
  "bing": {
    "bing_key": ""
  }
}
</pre></code>

## Usage
In Terminal:
<pre><code>
export FLASK_APP=/path_to/parse.py
flask run
</pre></code>
then:
<pre><code>
python3 main.py
</pre></code>
or using the ympd webclient

## Dependencies
- PyAudio
<pre><code>
sudo apt-get install portaudio19-dev

sudo pip3 install pyaudio
</pre></code>
- FLASK
<pre><code>
sudo pip3 install Flask
</pre></code>

- python-mpd2
<pre><code>
sudo pip3 install python-mpd2
</pre></code>
- monotonic
<pre><code>
sudo pip3 install monotonic
</pre></code>
- spacy (pip3 install spacy)
<pre><code>
sudo pip3 install spacy

download model for spacy:

sudo python3 -m spacy download en_core_web_lg
</pre></code>
- expiringdict
<pre><code>
sudo pip3 install expiringdict
</pre></code>

## Setting up the MPD Server
#### Linux
1. sudo apt-get install mpd
2. settings are described here https://wiki.ubuntuusers.de/MPD/Server/

#### Windows
1. Download the latest mpd.exe from http://www.musicpd.org/download/win32/
2. Create a folder mpd in C:/, e.g. C:/mpd
3. Insert the mpd.exe in C:/mpd
4. Create an empty mpd.db file in C:/mpd, e.g. mpd.db
5. Create an empty mpd.log file in C:/mpd, e.g. mpd.log
6. Create a folder music C:/mpd/music, where all music files placed in
7. Create a folder playlists C:/mpd/playlists, where all playlist files placed in
8. Create a mpd.conf file in C:/mpd with the following content
<pre><code>
music_directory "C:/mpd/music"
log_file "C:/mpd/mpd.log"
db_file "C:/mpd/mpd.db"
playlist_directory "C:/mpd/playlists"
audio_output {
    type "winmm"
    name "Speakers"
    device "Lautsprecher (Realtek High Definition Audio)"
}
audio_output {
    type "httpd"
    name "My HTTP Stream"
    encoder "vorbis" # optional, vorbis or lame
    port "8000"
    # quality "5.0" # do not define if bitrate is defined
    bitrate "128" # do not define if quality is defined
    format "44100:16:1"
}
</pre></code>
9. Open the terminal and go to the folder C:/mpd
<pre><code>
> cd C:/mpd
</pre></code>
10. Insert following command
<pre><code>
> mpd mpd.conf
</pre></code>

## Add Metadata to songs

Download MusicBrainz Picard from https://picard.musicbrainz.org/ and follow the instructions

## Project Layout
<pre><code>
/audio
    audio_data.py
    audio_file.py
    audio_file_stream.py
    microphone.py
    recognizer.py
    flac-linux-x86
    flac-linux-x86_64
    flac-mac

/configs
    configuration.json

/music_player
    mpd_connection.py

/nlp
    /service
        conversationState.py
        mpd_provider_module.py
        parse.py
        response.py
        verbalizer.py

/resources
    supported_languages.py

/speech_control
    speech_to_text.py
    text_to_speech.py

/ympd_webclient

LICENSE
main.py
README.md
setup.py
</pre></code>
