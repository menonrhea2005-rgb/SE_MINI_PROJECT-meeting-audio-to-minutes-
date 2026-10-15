
from dataclasses import dataclass
from pathlib import Path
import tempfile
import os

from audio_validator import AudioValidator


@dataclass
class ValidatedAudio:
    valid: bool
    format: str
    size: int
    message: str
    path: str | None = None


def validate_and_save(uploaded_file):
    """Validate an uploaded audio file and save it temporarily."""

    result = AudioValidator.validate(uploaded_file)

    if not result.valid:
        return ValidatedAudio(
            valid=False,
            format=result.format,
            size=result.size,
            message=result.message,
        )

    extension = Path(uploaded_file.name).suffix.lower()
    temp_path = None

    try:
        uploaded_file.seek(0)

        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:
            temp_path = temp_file.name

            while True:
                chunk = uploaded_file.read(1024 * 1024)

                if not chunk:
                    break

                temp_file.write(chunk)

        return ValidatedAudio(
            valid=True,
            format=result.format,
            size=result.size,
            message=result.message,
            path=temp_path,
        )

    except Exception:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        return ValidatedAudio(
            valid=False,
            format=result.format,
            size=result.size,
            message="Unable to prepare the audio file for transcription.",
        )


def cleanup_audio(audio):
    """Delete the temporary audio file when it is no longer needed."""

    if audio.path and os.path.exists(audio.path):
        os.remove(audio.path)
