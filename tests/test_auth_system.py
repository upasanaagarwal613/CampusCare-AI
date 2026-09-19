import os
import sys
import unittest
import json
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import create_app
from database.db import db
from backend.models import User, Provider

class TestAuthSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_student_registration(self):
        uid = uuid.uuid4().hex[:6]
        res = self.client.post("/api/auth/register", json={
            "name": f"Student {uid}",
            "email": f"student_{uid}@campus.edu",
            "password": "password123",
            "role": "student",
            "phone": "+1 (555) 333-4444"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["user"]["email"], f"student_{uid}@campus.edu")
        self.assertEqual(data["user"]["role"], "student")

    def test_02_provider_registration(self):
        uid = uuid.uuid4().hex[:6]
        res = self.client.post("/api/auth/register", json={
            "name": f"Tech {uid}",
            "email": f"tech_{uid}@campus.edu",
            "password": "password123",
            "role": "provider",
            "phone": "+1 (555) 777-8888",
            "service_category": "HVAC",
            "skills": ["Chillers", "Ductwork"]
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["user"]["role"], "provider")
        self.assertIsNotNone(data["user"]["provider_id"])

    def test_03_login_all_three_roles(self):
        # 1. Student Login
        res_stud = self.client.post("/api/auth/login", json={
            "email": "student2@campus.edu",
            "password": "student123",
            "portal_type": "user"
        })
        self.assertEqual(res_stud.status_code, 200)
        self.assertEqual(res_stud.get_json()["user"]["role"], "student")

        # 2. Provider Login
        res_prov = self.client.post("/api/auth/login", json={
            "email": "sparky@campus.edu",
            "password": "provider123",
            "portal_type": "provider"
        })
        self.assertEqual(res_prov.status_code, 200)
        self.assertEqual(res_prov.get_json()["user"]["role"], "provider")

        # 3. Admin Login
        res_adm = self.client.post("/api/auth/login", json={
            "email": "admin@campus.edu",
            "password": "admin123",
            "portal_type": "admin"
        })
        self.assertEqual(res_adm.status_code, 200)
        self.assertEqual(res_adm.get_json()["user"]["role"], "admin")

    def test_04_portal_type_mismatch_rejection(self):
        # Trying to login to admin portal with student credentials
        res = self.client.post("/api/auth/login", json={
            "email": "student2@campus.edu",
            "password": "student123",
            "portal_type": "admin"
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("error", res.get_json())

    def test_05_google_login(self):
        uid = uuid.uuid4().hex[:6]
        res = self.client.post("/api/auth/google-login", json={
            "email": f"google_{uid}@campus.edu",
            "name": f"Google Student {uid}",
            "role": "student"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["user"]["email"], f"google_{uid}@campus.edu")

    def test_06_forgot_password_otp_flow(self):
        # Register dedicated user for OTP test
        uid = uuid.uuid4().hex[:6]
        email = f"reset_user_{uid}@campus.edu"
        self.client.post("/api/auth/register", json={
            "name": "OTP Test User",
            "email": email,
            "password": "initial_password",
            "role": "student"
        })

        # Step A: Request OTP
        res_otp = self.client.post("/api/auth/forgot-password/send-otp", json={
            "email": email
        })
        self.assertEqual(res_otp.status_code, 200)
        data_otp = res_otp.get_json()
        self.assertIn("otp_demo", data_otp)
        otp = data_otp["otp_demo"]
        self.assertEqual(len(otp), 6)

        # Step B: Reset Password with OTP
        new_pw = "brand_new_secret_123"
        res_reset = self.client.post("/api/auth/forgot-password/verify-and-reset", json={
            "email": email,
            "otp": otp,
            "new_password": new_pw
        })
        self.assertEqual(res_reset.status_code, 200)

        # Step C: Log in with newly set password
        res_new_login = self.client.post("/api/auth/login", json={
            "email": email,
            "password": new_pw,
            "portal_type": "user"
        })
        self.assertEqual(res_new_login.status_code, 200)

if __name__ == "__main__":
    unittest.main()
