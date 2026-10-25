
import streamlit as st

from validated_audio import validate_and_save, cleanup_audio
from transcription import TranscriptionAdapter
from minutes_extractor import MinutesExtractor
from minutes_editor import MinutesEditor
from docx_exporter import DocxExporter


st.set_page_config(
    page_title="Meeting Audio to Structured Minutes",
    page_icon="🎙️",
    layout="wide",
)



@st.cache_resource(show_spinner=False)
def get_transcription_adapter():
    """Create the speech-to-text adapter once and reuse it.

    Loading the Whisper model is slow, so it stays in memory
    instead of being reloaded on every click (SRS MM-NF-001).
    """
    return TranscriptionAdapter()
st.title("Meeting Audio to Structured Minutes")
st.write(
    "Upload a meeting recording to generate a transcript, "
    "review the minutes, and download a Word document."
)

st.info(
    "Supported formats: WAV, MP3, M4A. Maximum file size: 100 MB."
)

uploaded_file = st.file_uploader(
    "Upload meeting audio",
    type=["wav", "mp3", "m4a"],
)

if uploaded_file is not None:
    st.write(f"**File:** {uploaded_file.name}")
    st.write(f"**Size:** {uploaded_file.size / (1024 * 1024):.2f} MB")

    if st.button("Validate Audio"):
        old_path = st.session_state.get("validated_audio_path")

        if old_path:
            from pathlib import Path

            if Path(old_path).is_file():
                Path(old_path).unlink()

        result = validate_and_save(uploaded_file)

        if result.valid:
            st.session_state["validated_audio_path"] = result.path
            st.session_state["validated_audio_name"] = uploaded_file.name
            st.session_state.pop("transcript", None)
            st.session_state.pop("minutes_draft", None)
            st.success(result.message)
        else:
            st.session_state.pop("validated_audio_path", None)
            st.error(result.message)

    if st.button("Transcribe Audio"):
        from pathlib import Path

        audio_path = st.session_state.get("validated_audio_path")
        saved_name = st.session_state.get("validated_audio_name")

        if saved_name != uploaded_file.name:
            st.warning("Please validate the currently selected file first.")
        elif not audio_path or not Path(audio_path).is_file():
            st.warning("Please validate the audio file first.")
        else:
            audio = type(
                "AudioForTranscription",
                (),
                {"valid": True, "path": audio_path},
            )()

            try:
                with st.spinner(
                    "Loading the speech model and transcribing audio..."
                ):
                    adapter = get_transcription_adapter()
                    result = adapter.transcribe(audio)

                st.session_state["transcript"] = result.text
                st.session_state["transcription_status"] = result.status

                if result.text:
                    st.success(result.status)
                else:
                    st.warning(result.status)

            except Exception as exc:
                st.error(str(exc))

    if "transcript" in st.session_state:
        st.subheader("Meeting Transcript")

        edited_transcript = st.text_area(
            "Review and edit the transcript",
            value=st.session_state["transcript"],
            height=250,
        )
        st.session_state["transcript"] = edited_transcript

        if st.button("Generate Meeting Minutes"):
            draft = MinutesExtractor.extract(edited_transcript)
            st.session_state["minutes_draft"] = draft
            st.success("Draft meeting minutes generated.")

    if "minutes_draft" in st.session_state:
        draft = st.session_state["minutes_draft"]

        st.subheader("Review Meeting Minutes")

        with st.form("minutes_form"):
            title = st.text_input(
                "Meeting title",
                value="Meeting Minutes",
            )

            topics_text = st.text_area(
                "Topics discussed (one per line)",
                value="\n".join(draft.topics),
            )

            decisions_text = st.text_area(
                "Decisions made (one per line)",
                value="\n".join(draft.decisions),
            )

            actions_text = st.text_area(
                "Action items (one per line)",
                value="\n".join(
                    f"{item.task} | Owner: {item.owner} | "
                    f"Deadline: {item.deadline}"
                    for item in draft.action_items
                ),
            )

            submitted = st.form_submit_button("Save Edited Minutes")

        if submitted:
            action_items = []

            from minutes_extractor import ActionItem

            for line in actions_text.splitlines():
                if line.strip():
                    parts = line.split("|")
                    task = parts[0].strip()
                    owner = "Not specified"
                    deadline = "Not specified"

                    for part in parts[1:]:
                        part = part.strip()

                        if part.lower().startswith("owner:"):
                            owner = part.split(":", 1)[1].strip()

                        elif part.lower().startswith("deadline:"):
                            deadline = part.split(":", 1)[1].strip()

                    action_items.append(
                        ActionItem(task, owner, deadline)
                    )

            edits = {
                "title": title,
                "topics": topics_text.splitlines(),
                "decisions": decisions_text.splitlines(),
                "action_items": action_items,
            }

            try:
                validated = MinutesEditor.validate_and_update(
                    draft, edits
                )
                st.session_state["validated_minutes"] = validated
                st.success("Your edited minutes have been saved.")
            except ValueError as exc:
                st.error(str(exc))

        if st.session_state.get("validated_minutes") is not None:
            validated = st.session_state["validated_minutes"]

            st.subheader("Download Meeting Minutes")

            document_bytes = DocxExporter.export(validated)

            st.download_button(
                label="Download Minutes as Word Document",
                data=document_bytes,
                file_name="Meeting_Minutes.docx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
            )

            if draft.review_flags:
                with st.expander("Items that may need your review"):
                    for flag in draft.review_flags:
                        st.write(f"- {flag}")
