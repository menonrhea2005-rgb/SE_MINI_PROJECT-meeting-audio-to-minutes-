"""UI tests for the Streamlit app (app.py).

These tests use Streamlit's built-in testing tool (AppTest), which runs
the page without a browser. They never load the real Whisper model:
the upload box and the speech-to-text adapter are replaced with small
fakes, so the tests are fast and work offline (including in CI).

Run them with:   python -m pytest test_app.py -v
"""

import tempfile
import tomllib
from pathlib import Path

from streamlit.testing.v1 import AppTest


PROJECT_DIR = Path(__file__).resolve().parent
APP_PATH = str(PROJECT_DIR / "app.py")

SAMPLE_TRANSCRIPT = (
    "Today we discussed the project report and the final demo. "
    "We decided to use Streamlit for the user interface. "
    "Saanvi will test the complete workflow by Friday. "
    "Someone needs to book the lab for the demo."
)


def run_app_with_fakes(
    app_path,
    upload_name=None,
    fake_transcript="",
    fail_export=False,
):
    """Start app.py with a fake upload and a fake transcription model.

    AppTest copies this function's source into a separate script, so
    everything it needs is imported inside the function.
    """
    import runpy
    import sys
    from pathlib import Path

    import streamlit as st

    project_dir = str(Path(app_path).parent)
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)

    import docx_exporter
    import transcription

    class FakeUpload:
        """Stands in for a file chosen in the upload box."""

        def __init__(self, name):
            self.name = name
            self.size = 1_200_000

    class FakeAdapter:
        """Returns a fixed transcript instead of running Whisper."""

        def transcribe(self, audio):
            return transcription.TranscriptResult(
                text=fake_transcript,
                status="Transcription completed successfully.",
            )

    def broken_export(minutes):
        raise RuntimeError("simulated export failure")

    st.file_uploader = lambda *args, **kwargs: (
        FakeUpload(upload_name) if upload_name else None
    )
    transcription.TranscriptionAdapter = FakeAdapter
    st.cache_resource.clear()

    if not hasattr(docx_exporter.DocxExporter, "real_export"):
        docx_exporter.DocxExporter.real_export = (
            docx_exporter.DocxExporter.export
        )

    docx_exporter.DocxExporter.export = staticmethod(
        broken_export
        if fail_export
        else docx_exporter.DocxExporter.real_export
    )

    runpy.run_path(app_path, run_name="__main__")


def make_app(**kwargs):
    """Create an AppTest for app.py with the given fake settings."""
    return AppTest.from_function(
        run_app_with_fakes,
        args=(APP_PATH,),
        kwargs=kwargs,
        default_timeout=30,
    )


def click(app, label):
    """Click the button with this label and re-run the page."""
    matches = [button for button in app.button if button.label == label]
    assert matches, f"No button labelled {label!r} on the page"
    matches[0].click()
    app.run()


def make_temp_audio():
    """Create an empty temporary .wav file and return its path."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as file:
        return file.name


def app_with_minutes(**kwargs):
    """An app that already has a transcript and generated minutes."""
    app = make_app(upload_name="meeting.wav", **kwargs)
    app.session_state["validated_audio_path"] = make_temp_audio()
    app.session_state["validated_audio_name"] = "meeting.wav"
    app.session_state["transcript"] = SAMPLE_TRANSCRIPT
    app.run()
    click(app, "Generate Meeting Minutes")
    return app


def progress_labels(app):
    """Text of the progress tracker row (✅ / 👉 / ⚪ steps)."""
    return [
        item.value
        for item in app.markdown
        if item.value.startswith(("✅", "👉", "⚪"))
    ]


# --- Upload screen (MM-F-001, MM-NF-002) ---------------------------------


def test_page_loads_with_upload_instructions():
    app = make_app()
    app.run()

    assert not app.exception
    assert app.title[0].value == "Meeting Audio to Structured Minutes"

    info = app.info[0].value
    assert "WAV, MP3, M4A" in info
    assert "100 MB" in info
    assert "WhatsApp" in info


def test_upload_limit_is_100_mb():
    config_path = PROJECT_DIR / ".streamlit" / "config.toml"

    with open(config_path, "rb") as config_file:
        config = tomllib.load(config_file)

    assert config["server"]["maxUploadSize"] == 100


# --- Validation and transcription (MM-F-004, MM-NF-003, SRS 3.1) --------


def test_progress_tracker_points_to_validation_first():
    app = make_app(upload_name="meeting.wav")
    app.run()

    labels = progress_labels(app)

    assert len(labels) == 4
    assert labels[0].startswith("👉") and "Validate audio" in labels[0]


def test_transcribe_before_validation_shows_warning():
    app = make_app(upload_name="meeting.wav")
    app.run()

    click(app, "Transcribe Audio")

    assert not app.exception
    assert any("validate" in w.value.lower() for w in app.warning)
    assert "transcript" not in app.session_state


def test_transcript_is_shown_after_transcription():
    app = make_app(
        upload_name="meeting.wav",
        fake_transcript=SAMPLE_TRANSCRIPT,
    )
    app.session_state["validated_audio_path"] = make_temp_audio()
    app.session_state["validated_audio_name"] = "meeting.wav"
    app.run()

    click(app, "Transcribe Audio")

    assert not app.exception
    transcript_box = [
        box for box in app.text_area
        if box.label == "Review and edit the transcript"
    ]
    assert transcript_box[0].value == SAMPLE_TRANSCRIPT
    assert progress_labels(app)[1].startswith("✅")


# --- Minutes review (MM-F-010, MM-F-011, MM-F-015) -----------------------


def test_empty_transcript_shows_warning():
    app = make_app(upload_name="meeting.wav")
    app.session_state["validated_audio_path"] = make_temp_audio()
    app.session_state["validated_audio_name"] = "meeting.wav"
    app.session_state["transcript"] = "   "
    app.run()

    click(app, "Generate Meeting Minutes")

    assert not app.exception
    assert any("transcript is empty" in w.value for w in app.warning)
    assert "minutes_draft" not in app.session_state


def test_minutes_sections_are_shown():
    app = app_with_minutes()

    assert not app.exception
    labels = [box.label for box in app.text_area]
    assert "Topics discussed (one per line)" in labels
    assert "Decisions made (one per line)" in labels
    assert any(item.value == "**Action items**" for item in app.markdown)


def test_missing_owner_and_deadline_are_flagged_not_invented():
    app = app_with_minutes()

    table = app.dataframe[0].value
    lab_row = table[table["Task"].str.contains("book the lab")].iloc[0]

    assert lab_row["Owner"] == ""
    assert lab_row["Deadline"] == ""
    assert "Confirm owner and deadline" in lab_row["Needs review"]
    assert any("need your review" in w.value for w in app.warning)


# --- Save and export (MM-F-012, MM-F-013, MM-F-014, MM-F-015) ------------


def test_save_keeps_task_owner_deadline_together():
    app = app_with_minutes()

    click(app, "Save Edited Minutes")

    assert not app.exception
    items = app.session_state["validated_minutes"].action_items
    saanvi = [item for item in items if item.task.startswith("Saanvi")][0]
    lab = [item for item in items if "book the lab" in item.task][0]

    assert (saanvi.owner, saanvi.deadline) == ("Saanvi", "by Friday")
    assert (lab.owner, lab.deadline) == ("Not specified", "Not specified")


def test_download_appears_after_save_with_last_saved_note():
    app = app_with_minutes()

    click(app, "Save Edited Minutes")

    assert len(app.get("download_button")) == 1
    assert any("last saved" in note.value for note in app.caption)
    assert all(label.startswith("✅") for label in progress_labels(app))


def test_export_failure_shows_message_instead_of_crashing():
    app = app_with_minutes(fail_export=True)

    click(app, "Save Edited Minutes")

    assert not app.exception
    assert any("Could not create the Word document" in e.value
               for e in app.error)
    assert len(app.get("download_button")) == 0


# --- Temporary files (MM-SR-003, SAD 3.1 step 8) -------------------------


def test_temp_audio_is_deleted_when_file_is_removed():
    temp_audio = make_temp_audio()

    app = make_app(upload_name=None)
    app.session_state["validated_audio_path"] = temp_audio
    app.session_state["validated_audio_name"] = "meeting.wav"
    app.run()

    assert not app.exception
    assert not Path(temp_audio).exists()
    assert "validated_audio_path" not in app.session_state