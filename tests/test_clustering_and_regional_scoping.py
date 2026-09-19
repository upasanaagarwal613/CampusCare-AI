import unittest
import json
from backend import create_app
from database.db import db
from backend.models import User, Complaint, Provider, Job, ComplaintCluster
from ml.clustering import dbscan_clusterer

class TestClusteringAndRegionalScoping(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_clustering_payload_contains_descriptions_and_counts(self):
        """Verify DBSCAN Volume and Severity clustering return problem_description, count, total_reports, and severity breakdown."""
        sample_complaints = [
            {
                "id": 101,
                "title": "Water leakage in 2nd floor washroom",
                "description": "Continuous water drip causing flooded corridor",
                "building": "Hostel Block A",
                "category": "Plumbing",
                "geo_lat": 27.4924,
                "geo_long": 77.6737,
                "predicted_urgency": "High",
                "college_name": "GLA University Mathura"
            },
            {
                "id": 102,
                "title": "Pipe joint cracked in 2nd floor sink",
                "description": "Pressure burst cracked PVC joint, water spraying onto wall",
                "building": "Hostel Block A",
                "category": "Plumbing",
                "geo_lat": 27.49245,
                "geo_long": 77.67375,
                "predicted_urgency": "Critical",
                "college_name": "GLA University Mathura"
            }
        ]

        # 1. Volume Clustering
        vol_res = dbscan_clusterer.run_clustering(sample_complaints, basis="volume")
        self.assertIn("clusters", vol_res)
        self.assertGreater(len(vol_res["clusters"]), 0)
        cl_vol = vol_res["clusters"][0]
        self.assertIn("count", cl_vol)
        self.assertEqual(cl_vol["count"], 2)
        self.assertIn("total_reports", cl_vol)
        self.assertEqual(cl_vol["total_reports"], 2)
        self.assertIn("problem_description", cl_vol)
        self.assertTrue(len(cl_vol["problem_description"]) > 10)
        self.assertIn("critical_count", cl_vol)
        self.assertEqual(cl_vol["critical_count"], 1)
        self.assertIn("high_count", cl_vol)
        self.assertEqual(cl_vol["high_count"], 1)

        # 2. Severity Clustering
        sev_res = dbscan_clusterer.run_clustering(sample_complaints, basis="severity")
        self.assertIn("clusters", sev_res)
        self.assertGreater(len(sev_res["clusters"]), 0)
        cl_sev = sev_res["clusters"][0]
        self.assertIn("count", cl_sev)
        self.assertEqual(cl_sev["count"], 2)
        self.assertIn("total_reports", cl_sev)
        self.assertEqual(cl_sev["total_reports"], 2)
        self.assertIn("problem_description", cl_sev)
        self.assertTrue(len(cl_sev["problem_description"]) > 10)
        self.assertIn("critical_count", cl_sev)
        self.assertEqual(cl_sev["critical_count"], 1)

    def test_mathura_admin_scoping(self):
        """Admin from GLA University Mathura MUST strictly receive Mathura GPS and complaints only."""
        with self.client:
            # Login as Mathura Admin
            login_res = self.client.post("/api/auth/login", json={
                "email": "admin.mathura@campus.edu",
                "password": "admin123"
            })
            self.assertEqual(login_res.status_code, 200)

            # Campus Map API must strictly center on Mathura
            map_res = self.client.get("/api/admin/campus-map")
            self.assertEqual(map_res.status_code, 200)
            map_data = json.loads(map_res.data)
            self.assertGreater(len(map_data), 0)
            first_b = map_data[0]
            self.assertEqual(first_b["college_name"], "GLA University Mathura")
            self.assertAlmostEqual(first_b["college_center"][0], 27.4924, places=2)
            self.assertAlmostEqual(first_b["college_center"][1], 77.6737, places=2)
            self.assertIn("problem_description", first_b)

            # Clusters API must strictly return Mathura complaints
            cluster_res = self.client.get("/api/admin/clusters?basis=volume")
            self.assertEqual(cluster_res.status_code, 200)

            # Complaints Desk API must strictly return Mathura complaints
            comp_res = self.client.get("/api/complaints")
            self.assertEqual(comp_res.status_code, 200)
            comps = json.loads(comp_res.data)
            for c in comps:
                self.assertEqual(c["college_name"], "GLA University Mathura")

    def test_meerut_admin_scoping(self):
        """Admin from MIET Meerut MUST strictly receive Meerut GPS and complaints only."""
        with self.client:
            # Login as Meerut Admin
            login_res = self.client.post("/api/auth/login", json={
                "email": "admin.meerut@campus.edu",
                "password": "admin123"
            })
            self.assertEqual(login_res.status_code, 200)

            # Campus Map API must strictly center on Meerut
            map_res = self.client.get("/api/admin/campus-map")
            self.assertEqual(map_res.status_code, 200)
            map_data = json.loads(map_res.data)
            self.assertGreater(len(map_data), 0)
            first_b = map_data[0]
            self.assertEqual(first_b["college_name"], "MIET Meerut")
            self.assertAlmostEqual(first_b["college_center"][0], 28.9845, places=2)
            self.assertAlmostEqual(first_b["college_center"][1], 77.7064, places=2)

            # Complaints Desk API must strictly return Meerut complaints
            comp_res = self.client.get("/api/complaints")
            self.assertEqual(comp_res.status_code, 200)
            comps = json.loads(comp_res.data)
            for c in comps:
                self.assertEqual(c["college_name"], "MIET Meerut")

if __name__ == "__main__":
    unittest.main()
