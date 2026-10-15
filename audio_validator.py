
from pathlib import Path
from dataclasses import dataclass

MAX_FILE_SIZE = 100 * 1024 * 1024

SUPPORTED_FORMATS = {
    ".wav": "WAV",
    ".mp3": "MP3",
    ".m4a": "M4A",
}


@dataclass
class ValidationResult:
    valid: bool
    format: str
    size: int
    message: str


class AudioValidator:

    @staticmethod
    def validate(file):
        filename = getattr(file, "name", "")
        extension = Path(filename).suffix.lower()

        if extension not in SUPPORTED_FORMATS:
            return ValidationResult(
                False, "", 0,
                "Unsupported file format. Upload WAV, MP3, or M4A."
            )

        try:
            file.seek(0)
            audio_data = file.read()
            file.seek(0)
        except Exception:
            return ValidationResult(
                False, SUPPORTED_FORMATS[extension], 0,
                "Unable to read the uploaded audio file."
            )

        size = len(audio_data)

        if size == 0:
            return ValidationResult(
                False, SUPPORTED_FORMATS[extension], 0,
                "The uploaded file is empty."
            )

        if size > MAX_FILE_SIZE:
            return ValidationResult(
                False, SUPPORTED_FORMATS[extension], size,
                "File exceeds the 100 MB size limit."
            )

        if not AudioValidator._has_valid_signature(
            extension, audio_data
        ):
            return ValidationResult(
                False, SUPPORTED_FORMATS[extension], size,
                "The file appears corrupted or is not a valid audio file."
            )

        return ValidationResult(
            True,
            SUPPORTED_FORMATS[extension],
            size,
            "Audio file validated successfully."
        )

    @staticmethod
    def _has_valid_signature(extension, data):
        if extension == ".wav":
            return (
                len(data) >= 12
                and data[:4] == b"RIFF"
                and data[8:12] == b"WAVE"
            )

        if extension == ".mp3":
            return (
                data.startswith(b"ID3")
                or (
                    len(data) >= 2
                    and data[0] == 0xFF
                    and (data[1] & 0xE0) == 0xE0
                )
            )

        if extension == ".m4a":
            return (
                len(data) >= 12
                and data[4:8] == b"ftyp"
            )

        return False
