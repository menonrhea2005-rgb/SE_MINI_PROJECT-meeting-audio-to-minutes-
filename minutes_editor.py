
from dataclasses import dataclass

from minutes_extractor import MinutesDraft, ActionItem


@dataclass
class ValidatedMinutes:
    title: str
    topics: list[str]
    decisions: list[str]
    action_items: list[ActionItem]


class MinutesEditor:

    @staticmethod
    def validate_and_update(draft, edits=None):
        """Validate and apply user edits to the meeting minutes."""

        edits = edits or {}

        if not isinstance(draft, MinutesDraft):
            raise ValueError("A valid minutes draft is required.")

        title = edits.get("title", "Meeting Minutes").strip()

        if not title:
            title = "Meeting Minutes"

        topics = edits.get("topics", draft.topics)
        decisions = edits.get("decisions", draft.decisions)
        action_items = edits.get("action_items", draft.action_items)

        if not isinstance(topics, list):
            raise ValueError("Topics must be provided as a list.")

        if not isinstance(decisions, list):
            raise ValueError("Decisions must be provided as a list.")

        if not isinstance(action_items, list):
            raise ValueError("Action items must be provided as a list.")

        if not all(isinstance(item, str) for item in topics):
            raise ValueError("Each topic must be text.")

        if not all(isinstance(item, str) for item in decisions):
            raise ValueError("Each decision must be text.")

        if not all(isinstance(item, ActionItem) for item in action_items):
            raise ValueError("Each action item must be valid.")

        return ValidatedMinutes(
            title=title,
            topics=[item.strip() for item in topics if item.strip()],
            decisions=[
                item.strip() for item in decisions if item.strip()
            ],
            action_items=action_items,
        )
