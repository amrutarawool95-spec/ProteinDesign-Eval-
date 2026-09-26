import unittest

from core.diversity import diversity_analysis
from core.ranking import rank_bundles, score_candidate
from core.sequence import pairwise_identity, sequence_metrics
from core.structure import structure_metrics


PDB = """HEADER    TEST
ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 50.00           N
ATOM      2  CA  ALA A   1       1.400   0.000   0.000  1.00 50.00           C
ATOM      3  C   ALA A   1       2.100   1.300   0.000  1.00 50.00           C
END
"""


class AnalysisTests(unittest.TestCase):
    def test_sequence_metrics(self):
        result = sequence_metrics("ACDE")
        self.assertEqual(result["length"], 4)
        self.assertAlmostEqual(result["charged_fraction"], 0.5)

    def test_identity_and_clustering(self):
        self.assertEqual(pairwise_identity("AAAA", "AAAA"), 1.0)
        result = diversity_analysis([
            {"candidate_id": "a", "sequence": "AAAA"},
            {"candidate_id": "b", "sequence": "AAAT"},
            {"candidate_id": "c", "sequence": "GGGG"},
        ], 0.75)
        self.assertEqual(result["redundancy_count"], 1)

    def test_structure_parser_has_no_plddt_from_bfactor(self):
        result = structure_metrics(PDB, "pdb")
        self.assertTrue(result["available"])
        self.assertIsNone(result["plddt"])
        self.assertEqual(result["atom_count"], 3)

    def test_rank_score_is_transparent(self):
        bundle = {"candidate_id": "x", "sequence": {"length": 10, "hydrophobic_fraction": 0.4}, "structure": {"available": True, "clash_count": 0}, "interface": {"available": True, "contacts": 8}, "specificity": {"available": False}, "conformation": {"available": False}, "diversity": {"cluster_sizes": {1: 1}}}
        result = score_candidate(bundle)
        self.assertIsNotNone(result["score"])
        self.assertIn("structure_quality", result["components"])
        self.assertEqual(rank_bundles([bundle])[0]["candidate_id"], "x")
