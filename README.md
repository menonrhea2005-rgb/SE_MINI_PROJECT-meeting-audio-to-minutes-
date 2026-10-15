\# SE Mini Project - Meeting Audio to Structured Meeting Minutes



\## Member 2: Audio Upload and Transcription



\### Overview

This module allows users to upload meeting audio, validates the uploaded file, converts speech into text using Faster-Whisper, and provides the transcript for the next stage of meeting-minutes generation.



\### Supported Audio Inputs

\- WAV (.wav)

\- MP3 (.mp3)

\- M4A (.m4a)



\### Audio Validation

The module checks:

\- Whether the uploaded file uses a supported extension.

\- Whether the file is empty.

\- Whether the file exceeds the 100 MB size limit.

\- Whether the file has a basic file signature consistent with its extension.



Files that fail validation are rejected with an error message.



\### Speech-to-Text Transcription

\- Library: Faster-Whisper

\- Model: base

\- Processing: Local CPU execution using int8 computation.

\- Output: Recognized speech as text for the meeting-minutes extraction module.



The first transcription may require downloading the model, so an internet connection may be needed initially. Subsequent runs can use the locally cached model.



\### Transcript Correction

The application allows users to review and edit the generated transcript before generating structured meeting minutes.



\### Error Handling

The workflow handles unsupported files, empty uploads, invalid audio inputs, and transcription failures with appropriate error messages.



\### Testing



Run the audio validation tests using:



```bash

python -m unittest test\_audio\_validator -v

```



Run the transcription tests using:



```bash

python -m unittest test\_transcription -v

```



Run the minutes extraction tests using:



```bash

python -m unittest test\_minutes\_extractor -v

```



Run all three test modules together using:



```bash

python -m unittest test\_audio\_validator test\_transcription test\_minutes\_extractor -v

```



All 16 automated tests passed during local testing.



\### Dependencies

Install the required Python packages using:



```bash

pip install -r requirements.txt

```



\### Notes

The audio validation checks file metadata and basic signatures; it does not guarantee that every file can be decoded successfully. Actual transcription depends on the audio content and the local environment.

