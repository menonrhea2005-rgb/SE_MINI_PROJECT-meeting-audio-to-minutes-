
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TranscriptResult:
    text: str
    status: str
    duration: float | None = None


class TranscriptionAdapter:
    """Converts a validated audio file into text using Faster-Whisper."""

    def __init__(self, model_size="base", device="cpu"):
        self.model_size = model_size
        self.device = device
        self.model = None

    def load_model(self):
        """Load the speech recognition model only when needed."""
        if self.model is not None:
            return

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "Faster-Whisper is not installed. "
                "Run: python -m pip install faster-whisper"
            ) from exc

        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="int8",
            )
        except Exception as exc:
            raise RuntimeError(
                "Could not load the transcription model. "
                "Check your installation and internet connection."
            ) from exc

    def transcribe(self, validated_audio):
        """Transcribe an audio file that has passed validation."""
        if not getattr(validated_audio, "valid", False):
            raise ValueError(
                "Audio must pass validation before transcription."
            )

        audio_path = getattr(validated_audio, "path", None)

        if not audio_path or not Path(audio_path).is_file():
            raise ValueError(
                "A valid audio file path is required for transcription."
            )

        self.load_model()

        try:
            segments, info = self.model.transcribe(
                str(audio_path),
                beam_size=5,
            )

            transcript_parts = [
                segment.text.strip()
                for segment in segments
                if segment.text.strip()
            ]

            transcript = " ".join(transcript_parts)

            if not transcript:
                return TranscriptResult(
                    text="",
                    status="No speech could be recognized.",
                    duration=getattr(info, "duration", None),
                )

            return TranscriptResult(
                text=transcript,
                status="Transcription completed successfully.",
                duration=getattr(info, "duration", None),
            )

        except Exception as exc:
            raise RuntimeError(
                "Transcription failed. Check whether the audio "
                "is readable and try again."
            ) from exc
