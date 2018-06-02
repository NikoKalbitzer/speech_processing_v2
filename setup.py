try:
    from setuptools import setup
    from setuptools.command.install import install
except ImportError:
    from distutils.core import setup
    from distutils.command.install import install
import platform
from subprocess import call


class PostInstallCommand(install):

    def run(self):
        system, machine = platform.system(), platform.machine()
        if system == "Windows" and machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
            install.run(self)
            call('py -3.5 -m pip install pyaudio'.split())
            call('py -3.5 -m pip install -r requirements.txt'.split())
            call('py -3.5 -m spacy download en_core_web_lg'.split())
        elif system == "Linux" and machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
            install.run(self)
            call('sudo apt-get install portaudio19-dev'.split())
            call('sudo pip3 install pyaudio'.split())
            call('sudo pip3 install -r requirements.txt'.split())
            call('sudo python3 -m spacy download en_core_web_lg'.split())


setup(
    name="speech_processing",
    description="A repository to control the mpd with speech",
    version="1.0",
    author="Bierschneider Christian, Martin Surner",
    author_email="christian1.bierschneider@st.oth-regensburg.de, martin.surner@st.oth-regensburg.de",
    py_modules=["speech_request_client", "definitions", "parse_server"],
    scripts=['requirements.txt'],
    packages=["audio", "configs", "music_player", "nlp", "nlp.locust", "nlp.service", "resources", "speech_control"],
    package_data={'audio': ['flac-linux-x86', 'flac-linux-x86_64', 'flac-mac', 'flac-win32.exe'],
                  'configs': ['*.json'], '': ['requirements.txt'], 'music_player': ['mpd.exe', 'radio_playlists/*.m3u']},
    install_requires=["monotonic", "python-mpd2", "spacy", "expiringdict", "Flask", "psutil"],
    cmdclass={
        'install': PostInstallCommand
    },
)

