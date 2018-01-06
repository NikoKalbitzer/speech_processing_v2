import io
import audioop
import os
import sys
import collections
import struct
import math
import threading
import uuid
import json
from audio.audio_file import AudioSource
from audio.audio_data import AudioData

try:  # attempt to use the Python 2 modules
    from urllib import urlencode
    from urllib2 import Request, urlopen, URLError, HTTPError
except ImportError:  # use the Python 3 modules
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError


class WaitTimeoutError(Exception): pass


class RequestError(Exception): pass


class UnknownValueError(Exception): pass


class PortableNamedTemporaryFile(object):
    """Limited replacement for ``tempfile.NamedTemporaryFile``, except unlike ``tempfile.NamedTemporaryFile``, the file can be opened again while it's currently open, even on Windows."""

    def __init__(self, mode="w+b"):
        self.mode = mode

    def __enter__(self):
        # create the temporary file and open it
        import tempfile
        file_descriptor, file_path = tempfile.mkstemp()
        self._file = os.fdopen(file_descriptor, self.mode)

        # the name property is a public field
        self.name = file_path
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._file.close()
        os.remove(self.name)

    def write(self, *args, **kwargs):
        return self._file.write(*args, **kwargs)

    def writelines(self, *args, **kwargs):
        return self._file.writelines(*args, **kwargs)

    def flush(self, *args, **kwargs):
        return self._file.flush(*args, **kwargs)


class Recognizer(AudioSource):
    def __init__(self):
        """
        Creates a new ``Recognizer`` instance, which represents a collection of speech recognition functionality.
        """
        self.energy_threshold = 300  # minimum audio energy to consider for recording
        self.dynamic_energy_threshold = True
        self.dynamic_energy_adjustment_damping = 0.15
        self.dynamic_energy_ratio = 1.5
        self.pause_threshold = 0.8  # seconds of non-speaking audio before a phrase is considered complete
        self.operation_timeout = None  # seconds after an internal operation (e.g., an API request) starts before it
                                       # times out, or ``None`` for no timeout

        self.phrase_threshold = 0.3  # minimum seconds of speaking audio before we consider the speaking audio a phrase
                                     # - values below this are ignored (for filtering out clicks and pops)

        self.non_speaking_duration = 0.5  # seconds of non-speaking audio to keep on both sides of the recording

    def record(self, source, duration=None, offset=None):
        """
        Records up to ``duration`` seconds of audio from ``source`` (an ``AudioSource`` instance) starting at ``offset``
        (or at the beginning if not specified) into an ``AudioData`` instance, which it returns.
        If ``duration`` is not specified, then it will record until there is no more audio input.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        assert source.stream is not None, "Audio source must be entered before recording, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"

        frames = io.BytesIO()
        seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
        elapsed_time = 0
        offset_time = 0
        offset_reached = False
        while True:  # loop for the total number of chunks needed
            if offset and not offset_reached:
                offset_time += seconds_per_buffer
                if offset_time > offset:
                    offset_reached = True

            buffer = source.stream.read(source.CHUNK)
            if len(buffer) == 0: break

            if offset_reached or not offset:
                elapsed_time += seconds_per_buffer
                if duration and elapsed_time > duration: break

                frames.write(buffer)

        frame_data = frames.getvalue()
        frames.close()
        return AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

    def adjust_for_ambient_noise(self, source, duration=1):
        """
        Adjusts the energy threshold dynamically using audio from ``source`` (an ``AudioSource`` instance) to account
        for ambient noise. Intended to calibrate the energy threshold with the ambient energy level. Should be used on
        periods of audio without speech - will stop early if any speech is detected. The ``duration`` parameter is the
        maximum number of seconds that it will dynamically adjust the threshold for before returning. This value should
         be at least 0.5 in order to get a representative sample of the ambient noise.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        assert source.stream is not None, "Audio source must be entered before adjusting, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"
        assert self.pause_threshold >= self.non_speaking_duration >= 0

        seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
        elapsed_time = 0

        # adjust energy threshold until a phrase starts
        while True:
            elapsed_time += seconds_per_buffer
            if elapsed_time > duration: break
            buffer = source.stream.read(source.CHUNK)
            energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # energy of the audio signal

            # dynamically adjust the energy threshold using asymmetric weighted average
            damping = self.dynamic_energy_adjustment_damping ** seconds_per_buffer  # account for different chunk sizes and rates
            target_energy = energy * self.dynamic_energy_ratio
            self.energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)

    def __wait_for_hot_word(self, snowboy_location, hot_words, source, timeout=None):
        """
        Blocks until a hot word, sometimes refered to as a wake word, it found in an audio input.
        Intended to be used as a means to limit network traffic and reduce cost of online speech-to-text services
        Currently utilizes the SnowBoy service which is free for hobbiest with a paid option for commerical use.
        ``snowboy_location`` is the local top level directory containing the compiled SnowBoy files.
        ``hot_words`` is an iterable element that contains the local file location of models provided by the SnowBoy
        service, either .pmdl or .umdl format ``source`` is the actual audio input as u
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        assert source.stream is not None, "Audio source must be entered before listening, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"
        assert snowboy_location is not None, "Need to specify snowboy_location argument if using hot words"
        assert os.path.isfile(snowboy_location + "/snowboydetect.py"), "Can not find snowboydetect.py. Make sure snowboy_location is pointed at the root directory"
        for f in hot_words: assert os.path.isfile(f), "Unable to locate file with given path: {}".format(f)

        sys.path.append(snowboy_location)
        import snowboydetect

        models = ",".join(hot_words)
        # get file path to needed resource file
        resource = snowboy_location + "/resources/common.res"
        detector = snowboydetect.SnowboyDetect(resource_filename=resource.encode(), model_str=models.encode())
        detector.SetAudioGain(1.0)
        sensitivity = [0.4] * len(hot_words)
        sensitivity_str = ",".join(str(t) for t in sensitivity)
        detector.SetSensitivity(sensitivity_str.encode())

        # create a deque to store our raw mic input data and one to store snowboy downsampled data, each hold 5sec of audio
        mic_buffer = collections.deque(maxlen=(source.SAMPLE_RATE * 5))
        sb_buffer = collections.deque(maxlen=(detector.SampleRate() * 5))

        # snowboy requires a specific sample rate that it provides, to avoid a ripple of issues we will just downsample momentarily by this ammount
        resample_ratio = float(source.SAMPLE_RATE) / float(detector.SampleRate())
        resample_count = 0

        seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
        elapsed_time = 0

        while True:
            # handle phrase being too long by cutting off the audio
            elapsed_time += seconds_per_buffer
            if timeout and elapsed_time > timeout:
                break

            buffer = source.stream.read(source.CHUNK)
            if len(buffer) == 0: break  # reached end of the stream

            # record mic data for use later
            mic_buffer.extend(buffer)

            # convert byte's into ints so we can downsample
            int_data = struct.unpack('<' + ('h' * (len(buffer) / source.SAMPLE_WIDTH)), buffer)
            ds_data = []

            # rough downsampling, can handle downsampling by non-integer values
            for i in range(len(int_data)):
                if resample_count <= 0:
                    sample = int_data[i]

                    # grab the previous sample too, but make sure we have one to grab
                    prev_sample = sample
                    if i != 0:
                        prev_sample = int_data[i - 1]

                    # get a number betwen 0 and 1, this is used to linearly interpolate between the two samples we have
                    ratio = 0.0 - resample_count
                    fab_sample = int((1.0 - ratio) * sample + (ratio) * prev_sample + 0.5)
                    ds_data.append(fab_sample)
                    resample_count += resample_ratio

                resample_count -= 1.0

            # convert back into bytes so we can feed it into snowboy
            sb_buffer.extend(struct.pack('<' + ('h' * len(ds_data)), *ds_data))

            # actually run the snowboy detector
            ans = detector.RunDetection(bytes(bytearray(sb_buffer)))
            assert ans != -1, "Error initializing streams or reading audio data"

            # if ans is greater than 0, we found a wake word! return audio
            if ans > 0:
                return bytes(mic_buffer), elapsed_time
        # return no sound bytes and add to timer
        return None, elapsed_time

    def listen(self, source, timeout=None, phrase_time_limit=None, hot_words=[], snowboy_location=None, wait_for_hot_word=False):
        """
        Records a single phrase from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance, which it
        returns. This is done by waiting until the audio has an energy above ``recognizer_instance.energy_threshold``
        (the user has started speaking), and then recording until it encounters ``recognizer_instance.pause_threshold``
        seconds of non-speaking or there is no more audio input. The ending silence is not included. The ``timeout``
        parameter is the maximum number of seconds that this will wait for a phrase to start before giving up and
        throwing an ``speech_recognition.WaitTimeoutError`` exception. If ``timeout`` is ``None``, there will be no wait
        timeout. The ``phrase_time_limit`` parameter is the maximum number of seconds that this will allow a phrase to
        continue before stopping and returning the part of the phrase processed before the time limit was reached. The
        resulting audio will be the phrase cut off at the time limit. If ``phrase_timeout`` is ``None``, there will be
        no phrase time limit. This operation will always complete within ``timeout + phrase_timeout`` seconds if both
        are numbers, either by returning the audio data, or by raising an exception.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        assert source.stream is not None, "Audio source must be entered before listening, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"
        assert self.pause_threshold >= self.non_speaking_duration >= 0

        # just make sure hot_words is iterable
        if not hasattr(hot_words, '__iter__'):
            hot_words = [hot_words]

        seconds_per_buffer = (source.CHUNK + 0.0) / source.SAMPLE_RATE
        pause_buffer_count = int(math.ceil(self.pause_threshold / seconds_per_buffer))  # number of buffers of non-speaking audio during a phrase, before the phrase should be considered complete
        phrase_buffer_count = int(math.ceil(self.phrase_threshold / seconds_per_buffer))  # minimum number of buffers of speaking audio before we consider the speaking audio a phrase
        non_speaking_buffer_count = int(math.ceil(self.non_speaking_duration / seconds_per_buffer))  # maximum number of buffers of non-speaking audio to retain before and after a phrase

        # read audio input for phrases until there is a phrase that is long enough
        elapsed_time = 0  # number of seconds of audio read
        buffer = b""  # an empty buffer means that the stream has ended and there is no data left to read
        while True:
            frames = collections.deque()

            # store audio input until the phrase starts
            while True:
                # handle waiting too long for phrase by raising an exception
                elapsed_time += seconds_per_buffer
                if timeout and elapsed_time > timeout:
                    raise WaitTimeoutError("listening timed out while waiting for phrase to start")

                buffer = source.stream.read(source.CHUNK)
                if len(buffer) == 0: break  # reached end of the stream
                frames.append(buffer)
                if len(frames) > non_speaking_buffer_count:  # ensure we only keep the needed amount of non-speaking buffers
                    frames.popleft()

                # detect whether speaking has started on audio input
                energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # energy of the audio signal
                if energy > self.energy_threshold: break

                # dynamically adjust the energy threshold using asymmetric weighted average
                if self.dynamic_energy_threshold:
                    damping = self.dynamic_energy_adjustment_damping ** seconds_per_buffer  # account for different chunk sizes and rates
                    target_energy = energy * self.dynamic_energy_ratio
                    self.energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)

            # read audio input until the phrase ends
            pause_count, phrase_count = 0, 0
            phrase_start_time = elapsed_time

            if wait_for_hot_word:
                audio_data, delta_time = self.__wait_for_hot_word(snowboy_location, hot_words, source, timeout)
                elapsed_time += delta_time
                if audio_data is None:
                    continue
                frames.append(audio_data)
            while True:
                # handle phrase being too long by cutting off the audio
                elapsed_time += seconds_per_buffer
                if phrase_time_limit and elapsed_time - phrase_start_time > phrase_time_limit:
                    break

                buffer = source.stream.read(source.CHUNK)
                if len(buffer) == 0: break  # reached end of the stream
                frames.append(buffer)
                phrase_count += 1

                # check if speaking has stopped for longer than the pause threshold on the audio input
                energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # unit energy of the audio signal within the buffer
                if energy > self.energy_threshold:
                    pause_count = 0
                else:
                    pause_count += 1
                if pause_count > pause_buffer_count:  # end of the phrase
                    break

            # check how long the detected phrase is, and retry listening if the phrase is too short
            phrase_count -= pause_count  # exclude the buffers for the pause before the phrase
            if phrase_count >= phrase_buffer_count or len(buffer) == 0: break  # phrase is long enough or we've reached the end of the stream, so stop listening

        # obtain frame data
        for i in range(pause_count - non_speaking_buffer_count): frames.pop()  # remove extra non-speaking frames at the end
        frame_data = b"".join(list(frames))

        return AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

    def listen_in_background(self, source, callback, phrase_time_limit=None):
        """
        Spawns a thread to repeatedly record phrases from ``source`` (an ``AudioSource`` instance) into an ``AudioData``
        instance and call ``callback`` with that ``AudioData`` instance as soon as each phrase are detected. Returns a
        function object that, when called, requests that the background listener thread stop, and waits until it does
        before returning. The background thread is a daemon and will not stop the program from exiting if there are no
        other non-daemon threads. Phrase recognition uses the exact same mechanism as
        ``recognizer_instance.listen(source)``. The ``phrase_time_limit`` parameter works in the same way as the
        ``phrase_time_limit`` parameter for ``recognizer_instance.listen(source)``, as well. The ``callback`` parameter
        is a function that should accept two parameters - the ``recognizer_instance``, and an ``AudioData`` instance
        representing the captured audio. Note that ``callback`` function will be called from a non-main thread.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        running = [True]

        def threaded_listen():
            with source as s:
                while running[0]:
                    try:  # listen for 1 second, then check again if the stop function has been called
                        audio = self.listen(s, 1, phrase_time_limit)
                    except WaitTimeoutError:  # listening timed out, just try again
                        pass
                    else:
                        if running[0]:
                            callback(audio)

        def stopper():
            running[0] = False
            listener_thread.join()  # block until the background thread is done, which can be up to 1 second

        listener_thread = threading.Thread(target=threaded_listen)
        listener_thread.daemon = True
        listener_thread.start()
        return stopper
        #return que.get()

    def recognize_bing(self, audio_data, key, language="en-US", show_all=False):
        """
        Performs speech recognition on ``audio_data`` (an ``AudioData`` instance), using the Microsoft Bing Speech API.
        The Microsoft Bing Speech API key is specified by ``key``. Unfortunately, these are not available without
        `signing up for an account <https://azure.microsoft.com/en-ca/pricing/details/cognitive-services/speech-api/>`__
        with Microsoft Azure. To get the API key, go to the `Microsoft Azure Portal Resources
        <https://portal.azure.com/>`__ page, go to "All Resources" > "Add" > "See All" > Search "Bing Speech API >
        "Create", and fill in the form to make a "Bing Speech API" resource. On the resulting page (which is also
        accessible from the "All Resources" page in the Azure Portal), go to the "Show Access Keys" page, which will
        have two API keys, either of which can be used for the `key` parameter. Microsoft Bing Speech API keys are
        32-character lowercase hexadecimal strings. The recognition language is determined by ``language``, a BCP-47
        language tag like ``"en-US"`` (US English) or ``"fr-FR"`` (International French), defaulting to US English. A
        list of supported language values can be found in the `API documentation <https://docs.microsoft.com/en-us/
        azure/cognitive-services/speech/api-reference-rest/bingvoicerecognition#recognition-language>`__
        under "Interactive and dictation mode". Returns the most likely transcription if ``show_all`` is false
        (the default). Otherwise, returns the `raw API response <https://docs.microsoft.com/en-us/azure/
        cognitive-services/speech/api-reference-rest/bingvoicerecognition#sample-responses>`__ as a JSON dictionary.
        Raises a ``speech_recognition.UnknownValueError`` exception if the speech is unintelligible. Raises a
        ``speech_recognition.RequestError`` exception if the speech recognition operation failed, if the key isn't
        valid, or if there is no internet connection.
        """
        assert isinstance(audio_data, AudioData), "Data must be audio data"
        assert isinstance(key, str),              "``key`` must be a string"
        assert isinstance(language, str),         "``language`` must be a string"

        access_token, expire_time = getattr(self, "bing_cached_access_token", None), \
                                    getattr(self, "bing_cached_access_token_expiry", None)
        allow_caching = True
        try:
            from time import \
                monotonic  # we need monotonic time to avoid being affected by system clock changes, but this is only available in Python 3.3+
        except ImportError:
            try:
                from monotonic import \
                    monotonic  # use time.monotonic backport for Python 2 if available (from https://pypi.python.org/pypi/monotonic)
            except (ImportError, RuntimeError):
                expire_time = None  # monotonic time not available, don't cache access tokens
                allow_caching = False  # don't allow caching, since monotonic time isn't available
        if expire_time is None or monotonic() > expire_time:  # caching not enabled, first credential request, or the access token from the previous one expired
            # get an access token using OAuth
            credential_url = "https://api.cognitive.microsoft.com/sts/v1.0/issueToken"
            credential_request = Request(credential_url, data=b"", headers={
                "Content-type": "application/x-www-form-urlencoded",
                "Content-Length": "0",
                "Ocp-Apim-Subscription-Key": key,
            })

            if allow_caching:
                start_time = monotonic()

            try:
                credential_response = urlopen(credential_request,
                                              timeout=60)  # credential response can take longer, use longer timeout instead of default one
            except HTTPError as e:
                raise RequestError("credential request failed: {}".format(e.reason))
            except URLError as e:
                raise RequestError("credential connection failed: {}".format(e.reason))
            access_token = credential_response.read().decode("utf-8")

            if allow_caching:
                # save the token for the duration it is valid for
                self.bing_cached_access_token = access_token
                self.bing_cached_access_token_expiry = start_time + 600  # according to https://docs.microsoft.com/en-us/azure/cognitive-services/speech/api-reference-rest/bingvoicerecognition, the token expires in exactly 10 minutes

        wav_data = audio_data.get_wav_data(
            convert_rate=16000,  # audio samples must be 8kHz or 16 kHz
            convert_width=2  # audio samples should be 16-bit
        )

        url = "https://speech.platform.bing.com/speech/recognition/interactive/cognitiveservices/v1?{}".format(
            urlencode({
                "language": language,
                "locale": language,
                "requestid": uuid.uuid4(),
            }))

        if sys.version_info >= (3,
                                6):  # chunked-transfer requests are only supported in the standard library as of Python 3.6+, use it if possible
            request = Request(url, data=io.BytesIO(wav_data), headers={
                "Authorization": "Bearer {}".format(access_token),
                "Content-type": "audio/wav; codec=\"audio/pcm\"; samplerate=16000",
                "Transfer-Encoding": "chunked",
            })
        else:  # fall back on manually formatting the POST body as a chunked request
            ascii_hex_data_length = "{:X}".format(len(wav_data)).encode("utf-8")
            chunked_transfer_encoding_data = ascii_hex_data_length + b"\r\n" + wav_data + b"\r\n0\r\n\r\n"
            request = Request(url, data=chunked_transfer_encoding_data, headers={
                "Authorization": "Bearer {}".format(access_token),
                "Content-type": "audio/wav; codec=\"audio/pcm\"; samplerate=16000",
                "Transfer-Encoding": "chunked",
            })

        try:
            response = urlopen(request, timeout=self.operation_timeout)
        except HTTPError as e:
            raise RequestError("recognition request failed: {}".format(e.reason))
        except URLError as e:
            raise RequestError("recognition connection failed: {}".format(e.reason))
        response_text = response.read().decode("utf-8")
        result = json.loads(response_text)

        # return results
        if show_all: return result
        if "RecognitionStatus" not in result or result[
            "RecognitionStatus"] != "Success" or "DisplayText" not in result: raise UnknownValueError()
        return result["DisplayText"]

    def recognize_sphinx(self, audio_data, language="en-US", keyword_entries=None, grammar=None, show_all=False):
        """
        Performs speech recognition on ``audio_data`` (an ``AudioData`` instance), using CMU Sphinx.
        The recognition language is determined by ``language``, an RFC5646 language tag like ``"en-US"`` or ``"en-GB"``, defaulting to US English. Out of the box, only ``en-US`` is supported. See `Notes on using `PocketSphinx <https://github.com/Uberi/speech_recognition/blob/master/reference/pocketsphinx.rst>`__ for information about installing other languages. This document is also included under ``reference/pocketsphinx.rst``. The ``language`` parameter can also be a tuple of filesystem paths, of the form ``(acoustic_parameters_directory, language_model_file, phoneme_dictionary_file)`` - this allows you to load arbitrary Sphinx models.
        If specified, the keywords to search for are determined by ``keyword_entries``, an iterable of tuples of the form ``(keyword, sensitivity)``, where ``keyword`` is a phrase, and ``sensitivity`` is how sensitive to this phrase the recognizer should be, on a scale of 0 (very insensitive, more false negatives) to 1 (very sensitive, more false positives) inclusive. If not specified or ``None``, no keywords are used and Sphinx will simply transcribe whatever words it recognizes. Specifying ``keyword_entries`` is more accurate than just looking for those same keywords in non-keyword-based transcriptions, because Sphinx knows specifically what sounds to look for.
        Sphinx can also handle FSG or JSGF grammars. The parameter ``grammar`` expects a path to the grammar file. Note that if a JSGF grammar is passed, an FSG grammar will be created at the same location to speed up execution in the next run. If ``keyword_entries`` are passed, content of ``grammar`` will be ignored.
        Returns the most likely transcription if ``show_all`` is false (the default). Otherwise, returns the Sphinx ``pocketsphinx.pocketsphinx.Decoder`` object resulting from the recognition.
        Raises a ``speech_recognition.UnknownValueError`` exception if the speech is unintelligible. Raises a ``speech_recognition.RequestError`` exception if there are any issues with the Sphinx installation.
        """
        assert isinstance(audio_data, AudioData), "``audio_data`` must be audio data"
        assert isinstance(language, str) or (isinstance(language, tuple) and len(language) == 3), "``language`` must be a string or 3-tuple of Sphinx data file paths of the form ``(acoustic_parameters, language_model, phoneme_dictionary)``"
        assert keyword_entries is None or all(isinstance(keyword, (type(""), type(u""))) and 0 <= sensitivity <= 1 for keyword, sensitivity in keyword_entries), "``keyword_entries`` must be ``None`` or a list of pairs of strings and numbers between 0 and 1"

        # import the PocketSphinx speech recognition module
        try:
            from pocketsphinx import pocketsphinx, Jsgf, FsgModel

        except ImportError:
            raise RequestError("missing PocketSphinx module: ensure that PocketSphinx is set up correctly.")
        except ValueError:
            raise RequestError("bad PocketSphinx installation; try reinstalling PocketSphinx version 0.0.9 or better.")
        if not hasattr(pocketsphinx, "Decoder") or not hasattr(pocketsphinx.Decoder, "default_config"):
            raise RequestError("outdated PocketSphinx installation; ensure you have PocketSphinx version 0.0.9 or better.")

        if isinstance(language, str):  # directory containing language data
            language_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "pocketsphinx-data", language)
            if not os.path.isdir(language_directory):
                raise RequestError("missing PocketSphinx language data directory: \"{}\"".format(language_directory))
            acoustic_parameters_directory = os.path.join(language_directory, "acoustic-model")
            language_model_file = os.path.join(language_directory, "language-model.lm.bin")
            phoneme_dictionary_file = os.path.join(language_directory, "pronounciation-dictionary.dict")
        else:  # 3-tuple of Sphinx data file paths
            acoustic_parameters_directory, language_model_file, phoneme_dictionary_file = language
        if not os.path.isdir(acoustic_parameters_directory):
            raise RequestError("missing PocketSphinx language model parameters directory: \"{}\"".format(acoustic_parameters_directory))
        if not os.path.isfile(language_model_file):
            raise RequestError("missing PocketSphinx language model file: \"{}\"".format(language_model_file))
        if not os.path.isfile(phoneme_dictionary_file):
            raise RequestError("missing PocketSphinx phoneme dictionary file: \"{}\"".format(phoneme_dictionary_file))

        # create decoder object
        config = pocketsphinx.Decoder.default_config()
        config.set_string("-hmm", acoustic_parameters_directory)  # set the path of the hidden Markov model (HMM) parameter files
        config.set_string("-lm", language_model_file)
        config.set_string("-dict", phoneme_dictionary_file)
        config.set_string("-logfn", os.devnull)  # disable logging (logging causes unwanted output in terminal)
        decoder = pocketsphinx.Decoder(config)

        # obtain audio data
        raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)  # the included language models require audio to be 16-bit mono 16 kHz in little-endian format

        # obtain recognition results
        if keyword_entries is not None:  # explicitly specified set of keywords
            with PortableNamedTemporaryFile("w") as f:
                # generate a keywords file - Sphinx documentation recommendeds sensitivities between 1e-50 and 1e-5
                f.writelines("{} /1e{}/\n".format(keyword, 100 * sensitivity - 110) for keyword, sensitivity in keyword_entries)
                f.flush()

                # perform the speech recognition with the keywords file (this is inside the context manager so the file isn;t deleted until we're done)
                decoder.set_kws("keywords", f.name)
                decoder.set_search("keywords")
                decoder.start_utt()  # begin utterance processing
                decoder.process_raw(raw_data, False, True)  # process audio data with recognition enabled (no_search = False), as a full utterance (full_utt = True)
                decoder.end_utt()  # stop utterance processing
        elif grammar is not None:  # a path to a FSG or JSGF grammar
            if not os.path.exists(grammar):
                raise ValueError("Grammar '{0}' does not exist.".format(grammar))
            grammar_path = os.path.abspath(os.path.dirname(grammar))
            grammar_name = os.path.splitext(os.path.basename(grammar))[0]
            fsg_path = "{0}/{1}.fsg".format(grammar_path, grammar_name)
            if not os.path.exists(fsg_path):  # create FSG grammar if not available
                jsgf = Jsgf(grammar)
                rule = jsgf.get_rule("{0}.{0}".format(grammar_name))
                fsg = jsgf.build_fsg(rule, decoder.get_logmath(), 7.5)
                fsg.writefile(fsg_path)
            else:
                fsg = FsgModel(fsg_path, decoder.get_logmath(), 7.5)
            decoder.set_fsg(grammar_name, fsg)
            decoder.set_search(grammar_name)
            decoder.start_utt()
            decoder.process_raw(raw_data, False, True)  # process audio data with recognition enabled (no_search = False), as a full utterance (full_utt = True)
            decoder.end_utt()  # stop utterance processing
        else:  # no keywords, perform freeform recognition
            decoder.start_utt()  # begin utterance processing
            decoder.process_raw(raw_data, False, True)  # process audio data with recognition enabled (no_search = False), as a full utterance (full_utt = True)
            decoder.end_utt()  # stop utterance processing

        if show_all: return decoder

        # return results
        hypothesis = decoder.hyp()
        if hypothesis is not None: return hypothesis.hypstr
        raise UnknownValueError()  # no transcriptions available

    def recognize_google(self, audio_data, key=None, language="en-US", show_all=False):
        """
        Performs speech recognition on ``audio_data`` (an ``AudioData`` instance), using the Google Speech Recognition API.
        The Google Speech Recognition API key is specified by ``key``. If not specified, it uses a generic key that works out of the box. This should generally be used for personal or testing purposes only, as it **may be revoked by Google at any time**.
        To obtain your own API key, simply following the steps on the `API Keys <http://www.chromium.org/developers/how-tos/api-keys>`__ page at the Chromium Developers site. In the Google Developers Console, Google Speech Recognition is listed as "Speech API".
        The recognition language is determined by ``language``, an RFC5646 language tag like ``"en-US"`` (US English) or ``"fr-FR"`` (International French), defaulting to US English. A list of supported language tags can be found in this `StackOverflow answer <http://stackoverflow.com/a/14302134>`__.
        Returns the most likely transcription if ``show_all`` is false (the default). Otherwise, returns the raw API response as a JSON dictionary.
        Raises a ``speech_recognition.UnknownValueError`` exception if the speech is unintelligible. Raises a ``speech_recognition.RequestError`` exception if the speech recognition operation failed, if the key isn't valid, or if there is no internet connection.
        """
        assert isinstance(audio_data, AudioData), "``audio_data`` must be audio data"
        assert key is None or isinstance(key, str), "``key`` must be ``None`` or a string"
        assert isinstance(language, str), "``language`` must be a string"

        flac_data = audio_data.get_flac_data(
            convert_rate=None if audio_data.sample_rate >= 8000 else 8000,  # audio samples must be at least 8 kHz
            convert_width=2  # audio samples must be 16-bit
        )
        if key is None: key = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
        url = "http://www.google.com/speech-api/v2/recognize?{}".format(urlencode({
            "client": "chromium",
            "lang": language,
            "key": key,
        }))
        request = Request(url, data=flac_data,
                          headers={"Content-Type": "audio/x-flac; rate={}".format(audio_data.sample_rate)})

        # obtain audio transcription results
        try:
            response = urlopen(request, timeout=self.operation_timeout)
        except HTTPError as e:
            raise RequestError("recognition request failed: {}".format(e.reason))
        except URLError as e:
            raise RequestError("recognition connection failed: {}".format(e.reason))
        response_text = response.read().decode("utf-8")

        # ignore any blank blocks
        actual_result = []
        for line in response_text.split("\n"):
            if not line: continue
            result = json.loads(line)["result"]
            if len(result) != 0:
                actual_result = result[0]
                break

        # return results
        if show_all: return actual_result
        if not isinstance(actual_result, dict) or len(
            actual_result.get("alternative", [])) == 0: raise UnknownValueError()

        if "confidence" in actual_result["alternative"]:
            # return alternative with highest confidence score
            best_hypothesis = max(actual_result["alternative"], key=lambda alternative: alternative["confidence"])
        else:
            # when there is no confidence available, we arbitrarily choose the first hypothesis.
            best_hypothesis = actual_result["alternative"][0]
        if "transcript" not in best_hypothesis: raise UnknownValueError()
        return best_hypothesis["transcript"]

