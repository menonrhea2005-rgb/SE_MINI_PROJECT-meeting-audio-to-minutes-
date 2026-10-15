
import io
import unittest

from audio_validator import AudioValidator


def make_wav():
    # Create a minimal WAV-like header for validation testing.
    return (
        b"RIFF"
        + (36).to_bytes(4, "little")
        + b"WAVE"
        + b"fmt "
        + b"\x10\x00\x00\x00"
        + b"\x01\x00\x01\x00"
        + (8000).to_bytes(4, "little")
        + (16000).to_bytes(4, "little")
        + b"\x02\x00\x10\x00"
        + b"data"
        + b"\x00\x00\x00\x00"
    )


class TestAudioValidator(unittest.TestCase):

    def test_supported_wav(self):
        file = io.BytesIO(make_wav())
        file.name = "meeting.wav"

        result = AudioValidator.validate(file)

        self.assertTrue(result.valid)
        self.assertEqual(result.format, "WAV")

    def test_unsupported_format(self):
        file = io.BytesIO(b"some content")
        file.name = "meeting.txt"

        result = AudioValidator.validate(file)

        self.assertFalse(result.valid)
        self.assertIn("Unsupported", result.message)

    def test_empty_file(self):
        file = io.BytesIO(b"")
        file.name = "meeting.wav"

        result = AudioValidator.validate(file)

        self.assertFalse(result.valid)
        self.assertIn("empty", result.message.lower())

    def test_corrupted_audio(self):
        file = io.BytesIO(b"not an audio file")
        file.name = "meeting.wav"

        result = AudioValidator.validate(file)

        self.assertFalse(result.valid)

    def test_file_over_100_mb(self):
        class LargeFile:
            name = "meeting.wav"

            def seek(self, position):
                pass

            def read(self):
                return b"x" * (100 * 1024 * 1024 + 1)

        result = AudioValidator.validate(LargeFile())

        self.assertFalse(result.valid)
        self.assertIn("100 MB", result.message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
