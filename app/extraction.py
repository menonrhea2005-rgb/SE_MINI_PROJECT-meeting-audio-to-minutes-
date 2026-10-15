
import re


def extract_minutes(transcript):
    """
    Extract discussion topics, decisions, and action items
    from a meeting transcript.
    """

    if not isinstance(transcript, str) or not transcript.strip():
        return {
            "topics": [],
            "decisions": [],
            "action_items": []
        }

    sentences = re.split(r'(?<=[.!?])\s+', transcript.strip())

    topics = []
    decisions = []
    action_items = []

    decision_keywords = [
        "decided", "approved", "agreed",
        "confirmed", "finalized"
    ]

    action_keywords = [
        "will", "must", "need to",
        "should", "responsible for",
        "assigned to"
    ]

    for sentence in sentences:
        text = sentence.strip()

        if not text:
            continue

        lower_text = text.lower()

        # Extract discussion topics
        if any(word in lower_text for word in [
            "discuss", "regarding", "about",
            "issue", "topic", "update", "review"
        ]):
            topics.append(text)

        # Extract explicit decisions
        if any(word in lower_text for word in decision_keywords):
            decisions.append(text)

        # Extract action items, owners, and deadlines
        if any(word in lower_text for word in action_keywords):

            owner = None
            deadline = None

            # Example: Priya will prepare the report
            owner_match = re.search(
                r'^([A-Z][a-z]+)\s+(?:will|must|should|need to)\s+',
                text
            )

            if owner_match:
                owner = owner_match.group(1)

            # Example: by Monday
            deadline_match = re.search(
                r'\bby\s+([A-Za-z]+(?:\s+\d{1,2})?)\b',
                text,
                re.IGNORECASE
            )

            if deadline_match:
                deadline = deadline_match.group(1)

            # Extract task description
            task = text

            if owner_match:
                task = text[owner_match.end():]

            task = re.sub(
                r'\s+by\s+[A-Za-z]+(?:\s+\d{1,2})?\b',
                '',
                task,
                flags=re.IGNORECASE
            ).strip().rstrip(".")

            action_items.append({
                "task": task,
                "owner": owner,
                "deadline": deadline
            })

    return {
        "topics": list(dict.fromkeys(topics)),
        "decisions": list(dict.fromkeys(decisions)),
        "action_items": action_items
    }
