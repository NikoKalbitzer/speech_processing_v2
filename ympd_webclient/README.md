Standalone MPD Web GUI written in C, utilizing Websockets and Bootstrap/JS

http://www.ympd.org


Dependencies
------------
 - libmpdclient 2: http://www.musicpd.org/libs/libmpdclient/
 - cmake 2.6: http://cmake.org/

Unix Build Instructions
-----------------------

1. install dependencies, cmake and libmpdclient are available from all major distributions.<br>
    ````sudo apt install cmake```` <br>
    Install libmpdclient with package manager: <br>
    ````sudo apt-get install libmpdclient-dev```` <br>
    Or install libmpdclient manually: <br>
    ````git clone https://github.com/MusicPlayerDaemon/libmpdclient.git```` <br>
    ````sudo apt install meson```` <br>
    ````meson .output```` <br>
    ````sudo su```` <br>
    ````ninja -C .output/```` <br>
    ````ninja -C .output/ install```` <br>
2. In ympd directory :<br>
   create build directory: <br>
   ```mkdir build; cd build```<br>
   check if c++ compiler is installed: <br>
   ````g++ --version````<br>
   install if no c++ compiler is available:<br>
   ````sudo apt install g++````<br>
   Install libssl-dev package:<br>
   ````sudo apt install libssl-dev````<br>
3. create makefile <br>
   ```cmake ..  -DCMAKE_INSTALL_PREFIX:PATH=/usr```
4. build <br>
   ```make```
5. install <br>
   ```sudo make install``` or just run with ```./ympd```

Run flags
---------
```
Usage: ./ympd [OPTION]...

 -h, --host <host>          connect to mpd at host [localhost]
 -p, --port <port>          connect to mpd at port [6600]
 -w, --webport [ip:]<port>  listen interface/port for webserver [8080]
 -u, --user <username>      drop priviliges to user after socket bind
 -V, --version              get version
 --help                     this help
```

