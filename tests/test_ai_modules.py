import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.classifier import nlp_classifier
from ml.clustering import dbscan_clusterer
from ml.matcher import provider_matcher

class TestAIModules(unittest.TestCase):
    def test_nlp_classification_electrical(self):
        result = nlp_classifier.classify("Sparks coming out of switchboard", "Circuit tripped and smoke smell")
        self.assertEqual(result["predicted_category"], "Electrical")
        self.assertIn(result["predicted_urgency"], ["Critical", "High"])
        self.assertGreater(result["confidence_score"], 0.4)
        self.assertTrue(any("spark" in kw or "smoke" in kw for kw in result["keywords_matched"]))

    def test_nlp_classification_plumbing(self):
        result = nlp_classifier.classify("Water pipe burst and bathroom flooding", "Water overflowing all over the floor")
        self.assertEqual(result["predicted_category"], "Plumbing")
        self.assertEqual(result["predicted_urgency"], "Critical")

    def test_dbscan_clustering(self):
        # 3 complaints in close proximity (Hostel Block A)
        sample_complaints = [
            {"id": 101, "geo_lat": 12.97150, "geo_long": 77.59450, "category": "Electrical", "building": "Hostel Block A"},
            {"id": 102, "geo_lat": 12.97152, "geo_long": 77.59452, "category": "Electrical", "building": "Hostel Block A"},
            {"id": 103, "geo_lat": 12.97155, "geo_long": 77.59453, "category": "Electrical", "building": "Hostel Block A"},
            # 1 distant isolated complaint (Science Complex)
            {"id": 104, "geo_lat": 12.97350, "geo_long": 77.59800, "category": "Plumbing", "building": "Science Complex"},
        ]

        cluster_res = dbscan_clusterer.run_clustering(sample_complaints)
        self.assertGreaterEqual(len(cluster_res["clusters"]), 1)
        cluster = cluster_res["clusters"][0]
        self.assertEqual(cluster["count"], 3)
        self.assertIn(101, cluster["complaint_ids"])
        self.assertIn(102, cluster["complaint_ids"])
        self.assertIn(103, cluster["complaint_ids"])
        self.assertIn(104, cluster_res["noise_ids"])

    def test_explainable_provider_matcher(self):
        complaint = {
            "category": "Electrical",
            "building": "Hostel Block A",
        }
        providers = [
            {
                "id": 1,
                "name": "Marcus Vance",
                "service_category": "Electrical",
                "skills": ["Circuits", "Wiring"],
                "rating": 4.9,
                "active_jobs_count": 0,
                "is_available": True,
                "location_zone": "Hostel Zone"
            },
            {
                "id": 2,
                "name": "Elena Rostova",
                "service_category": "Plumbing",
                "skills": ["Pipes"],
                "rating": 4.8,
                "active_jobs_count": 2,
                "is_available": True,
                "location_zone": "Central Zone"
            }
        ]

        ranked = provider_matcher.rank_providers(providers, complaint)
        self.assertEqual(len(ranked), 2)
        # Marcus Vance must be ranked top for Electrical
        self.assertEqual(ranked[0]["provider_id"], 1)
        self.assertGreater(ranked[0]["total_score"], ranked[1]["total_score"])
        # Check that score breakdown contains category, workload, rating, zone
        breakdown = ranked[0]["breakdown"]
        self.assertIn("category", breakdown)
        self.assertIn("workload", breakdown)
        self.assertIn("rating", breakdown)
        self.assertIn("zone", breakdown)
        self.assertEqual(breakdown["category"]["score"], 40)

if __name__ == "__main__":
    unittest.main()
