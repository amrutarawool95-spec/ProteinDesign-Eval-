import unittest

from core.feedback import normalize_feedback, summarize_feedback
from core.report import candidates_csv, feedback_template, project_json, project_zip


class FeedbackReportTests(unittest.TestCase):
    def test_feedback_summary_withholds_model(self):
        feedback = normalize_feedback([{"candidate_id": "a", "binding result": "positive"}, {"candidate_id": "b", "binding result": "negative"}])
        summary = summarize_feedback(feedback, [{"candidate_id": "a", "payload": {"sequence": {}, "structure": {}}}, {"candidate_id": "b", "payload": {"sequence": {}, "structure": {}}}])
        self.assertEqual(summary["n_success"], 1)
        self.assertFalse(summary["can_model"])

    def test_export_bytes(self):
        project = {"name": "test"}
        targets, candidates, analyses, feedback, audit = [], [{"candidate_id": "x", "sequence": "ACD"}], [], [], []
        self.assertIn(b"candidate_id", candidates_csv(candidates))
        self.assertIn(b"candidate_id", feedback_template())
        self.assertIn(b'"project"', project_json(project, targets, candidates, analyses, feedback, audit))
        self.assertTrue(project_zip(project, targets, candidates, analyses, feedback, audit).startswith(b"PK"))
