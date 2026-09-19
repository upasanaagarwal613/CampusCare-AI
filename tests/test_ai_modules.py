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
        self.assertTrue(ranked[0]["auto_assign_eligible"])
        self.assertIn("explanation", ranked[0])

    def test_eight_required_ml_examples(self):
        # 1. Structural crack in ceiling
        res1 = nlp_classifier.classify("The ceiling has a structural crack", "")
        self.assertEqual(res1["predicted_category"], "Civil & Structural")
        self.assertIn(res1["confidence_level"], ["High confidence", "Medium confidence"])

        # 2. Roof leaking during rain
        res2 = nlp_classifier.classify("The roof is leaking during rain", "")
        self.assertEqual(res2["predicted_category"], "Civil & Structural")

        # 3. Blocked toilet
        res3 = nlp_classifier.classify("The toilet is blocked", "")
        self.assertEqual(res3["predicted_category"], "Plumbing")
        self.assertEqual(res3["predicted_urgency"], "High")

        # 4. Burst pipe flooding bathroom
        res4 = nlp_classifier.classify("Water pipe has burst and the bathroom is flooding", "")
        self.assertEqual(res4["predicted_category"], "Plumbing")
        self.assertEqual(res4["predicted_urgency"], "Critical")

        # 5. Electrical switchboard sparking and exposed wires
        res5 = nlp_classifier.classify("Electrical switchboard is sparking and wires are exposed", "")
        self.assertEqual(res5["predicted_category"], "Electrical")
        self.assertEqual(res5["predicted_urgency"], "Critical")

        # 6. AC not cooling
        res6 = nlp_classifier.classify("The AC is not cooling", "")
        self.assertEqual(res6["predicted_category"], "HVAC")
        self.assertEqual(res6["predicted_urgency"], "High")

        # 7. Classroom chair broken
        res7 = nlp_classifier.classify("The classroom chair is broken", "")
        self.assertEqual(res7["predicted_category"], "Carpentry & Furniture")
        self.assertEqual(res7["predicted_urgency"], "High")

        # 8. Campus internet down
        res8 = nlp_classifier.classify("The campus internet is down", "")
        self.assertEqual(res8["predicted_category"], "Internet & IT")

    def test_provider_auto_assignment_threshold(self):
        complaint = {"category": "Electrical", "building": "Hostel Block A"}
        # High matching provider (should be >= 60 and auto-assign eligible)
        good_provider = {
            "id": 1, "name": "Marcus Vance", "service_category": "Electrical",
            "skills": ["Circuits"], "rating": 5.0, "active_jobs_count": 0,
            "is_available": True, "location_zone": "Hostel Zone"
        }
        good_score = provider_matcher.score_provider(good_provider, complaint)
        self.assertGreaterEqual(good_score["total_score"], 60)
        self.assertTrue(good_score["auto_assign_eligible"])

        # Completely mismatched provider (should be < 60 and not auto-assign eligible)
        bad_provider = {
            "id": 2, "name": "Elena Rostova", "service_category": "Sanitation",
            "skills": ["Cleaning"], "rating": 3.0, "active_jobs_count": 4,
            "is_available": True, "location_zone": "South Gate"
        }
        bad_score = provider_matcher.score_provider(bad_provider, complaint)
        self.assertLess(bad_score["total_score"], 60)
        self.assertFalse(bad_score["auto_assign_eligible"])

    def test_dbscan_explanation_preserved(self):
        sample = [
            {"id": 1, "geo_lat": 28.545, "geo_long": 77.193, "category": "Plumbing", "building": "Hostel Block A"},
            {"id": 2, "geo_lat": 28.5451, "geo_long": 77.1931, "category": "Plumbing", "building": "Hostel Block A"}
        ]
        res = dbscan_clusterer.run_clustering(sample, basis="volume")
        self.assertIn("explanation", res)
        self.assertIn("DBSCAN identifies spatially related complaint hotspots", res["explanation"])

if __name__ == "__main__":
    unittest.main()

