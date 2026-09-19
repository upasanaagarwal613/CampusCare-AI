import os
import sys
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import create_app

class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_preview_ai_endpoint(self):
        res = self.client.post("/api/complaints/preview-ai", json={
            "title": "Air conditioning unit leaking water and blowing hot air",
            "description": "Room is very humid and thermostat is not responding"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["predicted_category"], "HVAC")
        self.assertIn("urgency_score", data)
        self.assertIn("confidence_score", data)

    def test_create_complaint_and_clustering(self):
        res = self.client.post("/api/complaints", json={
            "student_id": 1,
            "title": "Corridor lights sparking dangerously",
            "description": "Sparking exposed wires on 2nd floor",
            "building": "Hostel Block A",
            "room_or_area": "2nd Floor Hallway",
            "category": "Auto-Detect"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["complaint"]["building"], "Hostel Block A")
        self.assertEqual(data["complaint"]["predicted_category"], "Electrical")

    def test_switch_demo_user(self):
        res = self.client.post("/api/auth/switch-demo", json={
            "email": "sparky@campus.edu"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["user"]["role"], "provider")
        self.assertEqual(data["user"]["name"], "Marcus Vance")

    def test_provider_recommendations_endpoint(self):
        # Pick complaint 1
        res = self.client.get("/api/providers/recommendations/1")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("recommendations", data)
        self.assertGreaterEqual(len(data["recommendations"]), 1)
        top = data["recommendations"][0]
        self.assertIn("total_score", top)
        self.assertIn("breakdown", top)

    def test_dbscan_run_endpoint(self):
        res = self.client.post("/api/admin/clusters/run-dbscan")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("clusters_detected", data)

if __name__ == "__main__":
    unittest.main()
