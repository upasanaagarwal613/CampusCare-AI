import unittest
import json
from backend import create_app
from database.db import db
from backend.models import User, Complaint

class TestFullMultiCampusWorkflow(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_end_to_end_mathura_vs_meerut_isolation(self):
        # 1. Login Mathura Admin
        res_m = self.client.post("/api/auth/login", json={
            "email": "admin.mathura@campus.edu",
            "password": "admin123"
        })
        self.assertEqual(res_m.status_code, 200)
        user_m = res_m.json["user"]
        self.assertEqual(user_m["college_name"], "GLA University Mathura")

        # Check Mathura Map Center
        map_m = self.client.get("/api/admin/campus-map").json
        self.assertGreater(len(map_m), 0)
        self.assertEqual(map_m[0]["college_name"], "GLA University Mathura")
        self.assertAlmostEqual(map_m[0]["college_center"][0], 27.4924, places=2)
        self.assertAlmostEqual(map_m[0]["college_center"][1], 77.6737, places=2)
        self.assertIn("problem_description", map_m[0])

        # Check Mathura Clusters
        cl_m = self.client.get("/api/admin/clusters?basis=volume").json["clusters"]
        self.assertGreater(len(cl_m), 0)
        self.assertEqual(cl_m[0]["count"], 2)
        self.assertIn("feeder panel", cl_m[0]["problem_description"].lower())

        # Logout Mathura Admin
        self.client.post("/api/auth/logout")

        # 2. Login Meerut Admin
        res_me = self.client.post("/api/auth/login", json={
            "email": "admin.meerut@campus.edu",
            "password": "admin123"
        })
        self.assertEqual(res_me.status_code, 200)
        user_me = res_me.json["user"]
        self.assertEqual(user_me["college_name"], "MIET Meerut")

        # Check Meerut Map Center
        map_me = self.client.get("/api/admin/campus-map").json
        self.assertGreater(len(map_me), 0)
        self.assertEqual(map_me[0]["college_name"], "MIET Meerut")
        self.assertAlmostEqual(map_me[0]["college_center"][0], 28.9845, places=2)
        self.assertAlmostEqual(map_me[0]["college_center"][1], 77.7064, places=2)

        # Check Meerut Clusters
        cl_me = self.client.get("/api/admin/clusters?basis=volume").json["clusters"]
        self.assertGreater(len(cl_me), 0)
        self.assertEqual(cl_me[0]["count"], 2)
        self.assertIn("water line", cl_me[0]["problem_description"].lower())

        # Verify Meerut Admin CANNOT see Mathura complaints
        comps_me = self.client.get("/api/complaints").json
        for c in comps_me:
            self.assertEqual(c["college_name"], "MIET Meerut")
            self.assertNotEqual(c["college_name"], "GLA University Mathura")

if __name__ == "__main__":
    unittest.main()
