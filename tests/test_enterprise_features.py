import os
import sys
import io
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import create_app
from database.db import db
from backend.models import User, Provider, Complaint, Job

class TestEnterpriseFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_admin_resolution_approval_signoff(self):
        """Tests Admin Done / Approval flow on a completed job."""
        with self.app.app_context():
            job = Job.query.filter_by(status="Completed").first()
            if not job:
                # Find any job and mark as Completed
                job = Job.query.first()
                job.status = "Completed"
                job.resolution_proof = "Replacement breaker installed"
                db.session.commit()

            job_id = job.id
            complaint_id = job.complaint_id

        # Admin approves the resolution
        res = self.client.post(f"/api/admin/jobs/{job_id}/approve", json={
            "notes": "Verified by Chief Facilities Officer"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["job"]["status"], "Approved")
        self.assertEqual(data["complaint"]["status"], "Closed / Verified")
        self.assertIsNotNone(data["job"]["admin_approved_at"])

    def test_02_emergency_sos_broadcast(self):
        """Tests Emergency SOS broadcast notification."""
        res = self.client.post("/api/admin/emergency-sos", json={
            "building": "Hostel Block A",
            "category": "Electrical Fire",
            "description": "Electrical junction box smoking heavily"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("Emergency SOS broadcast dispatched", data["message"])

    def test_03_provider_live_location_update(self):
        """Tests GPS location update for active session."""
        with self.client.session_transaction() as sess:
            # Login as provider
            with self.app.app_context():
                prov_user = User.query.filter_by(role="provider").first()
                sess["user_id"] = prov_user.id
                sess["role"] = "provider"

        res = self.client.post("/api/auth/update-live-location", json={
            "lat": 28.5455,
            "lng": 77.1935
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        with self.app.app_context():
            updated_prov = User.query.get(prov_user.id)
            self.assertEqual(updated_prov.live_lat, 28.5455)
            self.assertEqual(updated_prov.live_lng, 77.1935)
            self.assertEqual(updated_prov.provider_profile.current_lat, 28.5455)

    def test_04_student_complaint_privacy(self):
        """Verifies that a student can ONLY view their own filed complaints."""
        with self.app.app_context():
            student1 = User.query.filter_by(role="student").first()
            student1_id = student1.id
            # File a complaint under student1
            c = Complaint(
                student_id=student1_id,
                title="Privacy Test Ticket",
                description="Leaking pipe in my dorm room only",
                building="Hostel Block B",
                room_or_area="Room 210",
                college_name=student1.college_name or "IIT Delhi Main Campus",
                category="Plumbing",
                status="Submitted"
            )
            db.session.add(c)
            db.session.commit()
            target_id = c.id

        # Student 1 logs in
        with self.client.session_transaction() as sess:
            sess["user_id"] = student1_id
            sess["role"] = "student"

        res1 = self.client.get("/api/complaints")
        self.assertEqual(res1.status_code, 200)
        comps1 = res1.get_json()
        self.assertTrue(all(comp["student_id"] == student1_id for comp in comps1))
        self.assertIn(target_id, [comp["id"] for comp in comps1])

if __name__ == "__main__":
    unittest.main()
