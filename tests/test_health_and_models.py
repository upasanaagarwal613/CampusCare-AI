import os
import sys
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import create_app
from database.db import db
from backend.models import User, Provider, Complaint, Job, ComplaintCluster, Notification

class TestHealthAndModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_health_api(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database"], "connected")
        self.assertGreater(data["counts"]["users"], 0)
        self.assertGreater(data["counts"]["providers"], 0)
        self.assertGreater(data["counts"]["complaints"], 0)

    def test_models_exist_and_queryable(self):
        with self.app.app_context():
            # 1. User check
            users = User.query.all()
            self.assertGreaterEqual(len(users), 4)
            roles = set(u.role for u in users)
            self.assertIn("student", roles)
            self.assertIn("provider", roles)
            self.assertIn("admin", roles)

            # 2. Provider check
            providers = Provider.query.all()
            self.assertGreaterEqual(len(providers), 3)

            # 3. Complaint check
            complaints = Complaint.query.all()
            self.assertGreaterEqual(len(complaints), 3)

            # 4. Job check
            jobs = Job.query.all()
            self.assertGreaterEqual(len(jobs), 1)

            # 5. ComplaintCluster check
            clusters = ComplaintCluster.query.all()
            self.assertGreaterEqual(len(clusters), 1)

            # 6. Notification check
            notifs = Notification.query.all()
            self.assertGreaterEqual(len(notifs), 1)

if __name__ == "__main__":
    unittest.main()
