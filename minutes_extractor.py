
from dataclasses import dataclass, field
import re


@dataclass
class ActionItem:
    task: str
    owner: str = "Not specified"
    deadline: str = "Not specified"


@dataclass
class MinutesDraft:
    topics: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    review_flags: list[str] = field(default_factory=list)


class MinutesExtractor:
    """Extract possible meeting minutes using simple text rules."""

    TOPIC_CUES = (
        "discussed", "discussion", "meeting about",
        "agenda", "regarding", "project", "update",
    )

    DECISION_CUES = (
        "decided", "agreed", "approved",
        "we will", "it was decided", "decision",
    )

    ACTION_CUES = (
        "will", "must", "should", "needs to",
        "need to", "action item", "responsible for",
        "assigned to", "prepare", "complete", "submit",
    )

    DEADLINE_PATTERN = re.compile(
        r"\b(?:by|before|on)\s+"
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
        r"tomorrow|today|next week|next month|"
        r"\d{1,2}(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)|"
        r"\d{4}-\d{2}-\d{2})\b",
        re.IGNORECASE,
    )

    @staticmethod
    def _sentences(transcript):
        return [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", transcript.strip())
            if sentence.strip()
        ]

    @staticmethod
    def _contains_cue(sentence, cues):
        text = sentence.lower()
        return any(cue in text for cue in cues)

    @staticmethod
    def _find_owner(sentence):
        patterns = [
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+will\b",
            r"\bassigned to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
            r"\bresponsible for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, sentence)
            if match:
                return match.group(1)

        return "Not specified"

    @classmethod
    def extract(cls, transcript):
        draft = MinutesDraft()

        if not isinstance(transcript, str) or not transcript.strip():
            draft.review_flags.append(
                "No transcript was provided. Review the audio transcription."
            )
            return draft

        sentences = cls._sentences(transcript)

        for sentence in sentences:
            if cls._contains_cue(sentence, cls.TOPIC_CUES):
                draft.topics.append(sentence)

            if cls._contains_cue(sentence, cls.DECISION_CUES):
                draft.decisions.append(sentence)

            if cls._contains_cue(sentence, cls.ACTION_CUES):
                deadline_match = cls.DEADLINE_PATTERN.search(sentence)

                draft.action_items.append(
                    ActionItem(
                        task=sentence,
                        owner=cls._find_owner(sentence),
                        deadline=(
                            deadline_match.group(0)
                            if deadline_match
                            else "Not specified"
                        ),
                    )
                )

        if not draft.topics:
            draft.review_flags.append(
                "No clear topics were detected. Review the transcript."
            )

        if not draft.decisions:
            draft.review_flags.append(
                "No explicit decisions were detected."
            )

        if not draft.action_items:
            draft.review_flags.append(
                "No clear action items were detected."
            )

        for item in draft.action_items:
            if item.owner == "Not specified":
                draft.review_flags.append(
                    f"Confirm the owner for this action: {item.task}"
                )

            if item.deadline == "Not specified":
                draft.review_flags.append(
                    f"Confirm the deadline for this action: {item.task}"
                )

        return draft
