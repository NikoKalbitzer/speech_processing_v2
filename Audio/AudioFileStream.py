import audioop


class AudioFileStream(object):
    def __init__(self, audio_reader, little_endian, samples_24_bit_pretending_to_be_32_bit):
        self.audio_reader = audio_reader  # an audio file object (e.g., a `wave.Wave_read` instance)
        self.little_endian = little_endian  # whether the audio data is little-endian (when working with big-endian things, we'll have to convert it to little-endian before we process it)
        self.samples_24_bit_pretending_to_be_32_bit = samples_24_bit_pretending_to_be_32_bit  # this is true if the audio is 24-bit audio, but 24-bit audio isn't supported, so we have to pretend that this is 32-bit audio and convert it on the fly

    def read(self, size=-1):
        buffer = self.audio_reader.readframes(self.audio_reader.getnframes() if size == -1 else size)
        if not isinstance(buffer, bytes): buffer = b""  # workaround for https://bugs.python.org/issue24608

        sample_width = self.audio_reader.getsampwidth()
        if not self.little_endian:  # big endian format, convert to little endian on the fly
            if hasattr(audioop,
                       "byteswap"):  # ``audioop.byteswap`` was only added in Python 3.4 (incidentally, that also means that we don't need to worry about 24-bit audio being unsupported, since Python 3.4+ always has that functionality)
                buffer = audioop.byteswap(buffer, sample_width)
            else:  # manually reverse the bytes of each sample, which is slower but works well enough as a fallback
                buffer = buffer[sample_width - 1::-1] + b"".join(
                    buffer[i + sample_width:i:-1] for i in range(sample_width - 1, len(buffer), sample_width))

        # workaround for https://bugs.python.org/issue12866
        if self.samples_24_bit_pretending_to_be_32_bit:  # we need to convert samples from 24-bit to 32-bit before we can process them with ``audioop`` functions
            buffer = b"".join(b"\x00" + buffer[i:i + sample_width] for i in range(0, len(buffer),
                                                                                  sample_width))  # since we're in little endian, we prepend a zero byte to each 24-bit sample to get a 32-bit sample
            sample_width = 4  # make sure we thread the buffer as 32-bit audio now, after converting it from 24-bit audio
        if self.audio_reader.getnchannels() != 1:  # stereo audio
            buffer = audioop.tomono(buffer, sample_width, 1, 1)  # convert stereo audio data to mono
        return buffer