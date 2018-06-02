import platform
import os
import subprocess
import signal
import psutil
import re
import logging as log
from definitions import ROOT_DIR

class LoadMPD:

    def __init__(self):
        """
        constructor to init variables and call the self.find_os() method
        """
        self.mpd_pid = None
        self.system = platform.system()
        self.machine = platform.machine()
        self.find_os()

    def __del__(self):
        """
        destructor
        """

    def find_os(self):
        """
        depending on the system and machine load the correct mpd server
        """
        if self.system == "Windows" and self.machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
            log.info("windows system")
            self.create_files_win(ROOT_DIR)
            mpd_exe_path = os.path.join(ROOT_DIR, "music_player\mpd.exe")
            mpd_conf_path = os.path.join(ROOT_DIR, "music_player\mpd.conf")

            if not self.is_mpd_running_win():
                log.info("start mpd.exe")
                self.start_mpd_win(mpd_exe_path, mpd_conf_path)
            else:
                log.info("mpd.exe is running")

        elif self.system == "Linux" and self.machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
            log.info("linux system")
            if not self.is_mpd_running_linux():
                self.start_mpd_linux()
            else:
                log.info("mpd is running")

        """
        elif system == "Darwin" and machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
            flac_converter = os.path.join(base_path, "flac-mac")

        """
    # Windows machines

    def create_files_win(self, base_path):
        """
        method to check if mpd.conf, mpd.log, mpd.db are exists. If not, then create these files

        :param base_path, path for creating these files
        """
        log.info("create files for windows machines")
        if not os.path.exists('music_player/songs'):
            os.makedirs('music_player/songs')
        music_directory = os.path.join(base_path, 'music_player\songs')
        music_directory = '/'.join(music_directory.split('\\'))
        if not os.path.exists('music_player/radio_playlists'):
            os.makedirs('music_player/radio_playlists')
        playlist_directory = os.path.join(base_path, 'music_player\\radio_playlists')
        playlist_directory = '/'.join(playlist_directory.split('\\'))
        mpd_conf_path = os.path.join(base_path, 'music_player\mpd.conf')

        mpd_log_path = os.path.join(base_path, 'music_player\mpd.log')
        mpd_log_path = '/'.join(mpd_log_path.split('\\'))

        mpd_db_path = os.path.join(base_path, 'music_player\mpd.db')
        mpd_db_path = '/'.join(mpd_db_path.split('\\'))

        if not os.path.exists(mpd_log_path):
            log.info("create log file")
            open(mpd_log_path, 'w')
        if not os.path.exists(mpd_db_path):
            log.info("create db file")
            open(mpd_db_path, 'w')
        if not os.path.exists(mpd_conf_path):
            log.info("create mpd conf file")
            with open(mpd_conf_path, 'w') as mpd_conf:
                mpd_conf.writelines("music_directory " + "\"" + music_directory + "\"" + "\n" +
                                    "playlist_directory " + "\"" + playlist_directory + "\"" + "\n" +
                                    "log_file " + "\"" + mpd_log_path + "\"" + "\n" +
                                    "db_file " + "\"" + mpd_db_path + "\"" + "\n" + "\n")

                mpd_conf.writelines("audio_output {" + "\n" + "    type \"winmm\"" + "\n" + "    name \"Speakers\"" + "\n" +
                                    "    device \"Lautsprecher (High Definition Audio-Gerät)\"" + "\n" + "}" + "\n")

                mpd_conf.writelines("audio_output {" + "\n" + "    type \"httpd\"" + "\n" + "    name \"My HTTP Stream\"" + "\n"
                                      "    encoder \"vorbis\" # optional, vorbis or lame" + "\n" + "    port \"8000\"" + "\n"
                                    + "    # quality \"5.0\" # do not define if bitrate is defined" + "\n"
                                    + "    bitrate \"128\" # do not define if quality is defined" + "\n"
                                    + "    format \"44100:16:1\"" + "\n" + "}")

    @staticmethod
    def is_mpd_running_win():
        """
        checks if the mpd server is already running

        :return: "False" if no mpd server is running
        """
        return "mpd.exe" in (p.name() for p in psutil.process_iter())

    def start_mpd_win(self, mpd_exe_path, mpd_conf_path):
        """
        starts the mpd.exe as a background process on windows machines

        :param mpd_exe_path: path to the ./mpd.exe file
        :param mpd_conf_path: path to the ./mpd.conf configuration file
        """
        log.info("start subprocess for mpd.exe")
        DETACHED_PROCESS = 0x00000008

        self.mpd_pid = subprocess.Popen([mpd_exe_path, mpd_conf_path], creationflags=DETACHED_PROCESS).pid

    @staticmethod
    def kill_mpd_process_win():
        """
        static method to kill all mpd processes on windows machines

        """
        print("kill")
        if platform.system() == "Windows" and platform.machine() in {"i686", "i786", "x86", "x86_64", "AMD64"}:
            log.info("kill all mpd.exe on windows")
            mpd_processes = [p.pid for p in psutil.process_iter(attrs=['pid', 'name']) if 'mpd.exe' in p.info['name']]
            for proc in mpd_processes:
                os.kill(proc, signal.SIGTERM)

    # linux machines

    @staticmethod
    def is_mpd_running_linux():
        """
        checks if the mpd server is already running
        :return: "False" if no mpd server is running
        """
        return "mpd" in (p.name() for p in psutil.process_iter())

    def start_mpd_linux(self):
        """
        package mpd is being installed, if not already available. After installation mpd process start automatically,
        if not then mpd service will be started

        """
        log.info("start subprocess for mpd on linux")
        p = subprocess.Popen(["apt", "list", "mpd"], stdout=subprocess.PIPE)
        outs, errs = p.communicate()
        if errs is None:
            if b"installed" in outs:
                log.info("mpd package is installed")
                #self.change_path_mpd()
                if not self.is_mpd_running_linux():
                    log.info("start mpd service on linux")
                    subprocess.call(["sudo", "service", "mpd", "start"])
            else:
                log.info("package mpd is being installed")
                subprocess.call(["sudo", "apt-get", "install", "mpd"])
        else:
            log.info("error for communicating with the subprocess \"apt list mpd\"")

        #self.mpd_pid = subprocess.Popen([mpd_exe_path, mpd_conf_path], creationflags=DETACHED_PROCESS).pid

    def change_path_mpd(self):
        """

        :return:
        """
        new_path = '\"' + ROOT_DIR + '/music_player/songs/' + '\"'

        file_handle = open('/etc/mpd.conf', 'r')
        mpd_conf_string = file_handle.read()
        file_handle.close()

        new_mpd_conf_string = (re.sub('\"/var/lib/mpd/music\"', new_path, mpd_conf_string))
        file_handle = open('/etc/mpd.conf', 'w')
        file_handle.write(new_mpd_conf_string)
        file_handle.close()
        log.info("restart mpd service on linux")
        subprocess.call(["sudo", "service", "mpd", "restart"])


if __name__ == '__main__':
    LoadMPD()
