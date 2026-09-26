import unittest

from core.validation import parse_candidate_csv, parse_fasta, parse_candidate_json


class ValidationTests(unittest.TestCase):
    def test_fasta_rejects_invalid_and_duplicates(self):
        records, issues = parse_fasta(">a\nACD*\n>a\n")
        self.assertEqual(len(records), 2)
        self.assertTrue(any("Invalid" in issue.message for issue in issues))
        self.assertTrue(any("Duplicate" in issue.message for issue in issues))

    def test_csv_missing_columns(self):
        rows, issues = parse_candidate_csv("id,sequence\nx,ACD\n")
        self.assertEqual(rows, [])
        self.assertIn("Missing required columns", issues[0].message)

    def test_json_candidate_list(self):
        rows, issues = parse_candidate_json('[{"candidate_id":"x","sequence":"ACDE"}]')
        self.assertEqual(len(rows), 1)
        self.assertFalse([i for i in issues if i.level == "error"])
