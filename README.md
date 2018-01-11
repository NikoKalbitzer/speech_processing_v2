# Speech processing
Forked from https://github.com/Uberi/speech_recognition

A repository to control the mpd server with speech:
- Speech to Text
- Text to Speech
- Audio files
- Natural Language Processing
- Speech control of the MPD
## Usage

## Dependencies
- PyAudio (pip3 install pyaudio, apt-get install portaudio19-dev)
- python-mpd2 (pip3 install python-mpd2)
- monotonic (pip3 install monotonic)
- spacy (pip3 install spacy)
   - download model for spacy: python3 -m spacy download en_core_web_lg
- expiringdict (pip3 install expiringdict)

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

/MPD_NLP
    /service
        conversationState.py
        mpd_provider_module.py
        parse.py
        response.py
        verbalizer.py

/mpd
    mpd_connection.py

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
