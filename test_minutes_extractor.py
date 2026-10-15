
import unittest

from minutes_extractor import MinutesExtractor


class TestMinutesExtractor(unittest.TestCase):

    def test_extract_topic(self):
        transcript = "We discussed the project timeline."
        result = MinutesExtractor.extract(transcript)

        self.assertTrue(len(result.topics) > 0)

    def test_extract_decision(self):
        transcript = "We decided to use Python."
        result = MinutesExtractor.extract(transcript)

        self.assertTrue(len(result.decisions) > 0)

    def test_extract_action_item(self):
        transcript = "Ravi will submit the report by Friday."
        result = MinutesExtractor.extract(transcript)

        self.assertTrue(len(result.action_items) > 0)

    def test_extract_owner(self):
        transcript = "Ravi will submit the report by Friday."
        result = MinutesExtractor.extract(transcript)

        self.assertEqual(result.action_items[0].owner, "Ravi")

    def test_extract_deadline(self):
        transcript = "Ravi will submit the report by Friday."
        result = MinutesExtractor.extract(transcript)

        self.assertEqual(
            result.action_items[0].deadline,
            "by Friday"
        )

    def test_empty_transcript(self):
        result = MinutesExtractor.extract("")

        self.assertTrue(len(result.review_flags) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
