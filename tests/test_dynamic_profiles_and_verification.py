import os
import sys
import io
import uuid
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import create_app
from backend.models import User, Provider, Complaint, Job
from database.db import db


class TestDynamicProfilesAndVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_student_registration_zero_baseline(self):
        # 1. Register fresh student
        uid = uuid.uuid4().hex[:6]
        email = f'student.{uid}@campus.edu'
        res = self.client.post('/api/auth/register', json={
            'name': f'Kavita Rao {uid}',
            'email': email,
            'password': 'password123',
            'role': 'student',
            'phone': '+1 (555) 777-1111'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()['user']
        self.assertEqual(data['name'], f'Kavita Rao {uid}')
        self.assertEqual(data['role'], 'student')
        self.assertEqual(data['total_complaints_filed'], 0)

    def test_02_provider_registration_multi_specialties(self):
        # 2. Register multi-specialty technician
        uid = uuid.uuid4().hex[:6]
        email = f'tech.{uid}@campus.edu'
        res = self.client.post('/api/auth/register', json={
            'name': f'Ramesh Kumar {uid}',
            'email': email,
            'password': 'password123',
            'role': 'provider',
            'phone': '+1 (555) 777-2222',
            'service_category': 'Electrical, HVAC, Plumbing'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()['user']
        self.assertEqual(data['name'], f'Ramesh Kumar {uid}')
        self.assertEqual(data['role'], 'provider')
        self.assertIn('Electrical', data['service_category'])
        self.assertIn('HVAC', data['service_category'])
        self.assertIn('Plumbing', data['service_category'])
        self.assertEqual(data['active_jobs_count'], 0)
        self.assertEqual(data['total_jobs_completed'], 0)

    def test_03_admin_registration_with_teacher_card(self):
        # 3. Register admin with Teacher Card proof upload
        card_bytes = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c434')
        uid = uuid.uuid4().hex[:6]
        email = f'dean.{uid}@campus.edu'
        res = self.client.post('/api/auth/register', data={
            'name': f'Prof. H. S. Sharma {uid}',
            'email': email,
            'password': 'password123',
            'role': 'admin',
            'phone': '+1 (555) 777-3333',
            'designation': 'Dean of Student Welfare',
            'staff_id_number': f'FAC-{uid}',
            'teacher_id_card': (io.BytesIO(card_bytes), 'faculty_card.png')
        }, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 201)
        data = res.get_json()['user']
        self.assertEqual(data['name'], f'Prof. H. S. Sharma {uid}')
        self.assertEqual(data['role'], 'admin')
        self.assertEqual(data['designation'], 'Dean of Student Welfare')
        self.assertEqual(data['staff_id_number'], f'FAC-{uid}')
        self.assertIsNotNone(data['id_card_url'])
        self.assertTrue(data['id_card_url'].startswith('/static/uploads/'))

    def test_04_automatic_provider_assignment_and_solution_proof(self):
        # 4. Student files an electrical complaint
        res_comp = self.client.post('/api/complaints', data={
            'title': 'Severe Sparks in Switchboard Hostel Block A',
            'description': 'Main breaker panel sparking heavily near room 101',
            'building': 'Hostel Block A',
            'room_or_area': 'Room 101',
            'category': 'Electrical'
        })
        self.assertEqual(res_comp.status_code, 201)
        c_data = res_comp.get_json()['complaint']
        self.assertEqual(c_data['status'], 'Assigned')
        self.assertIsNotNone(c_data['job'])
        job_id = c_data['job']['id']

        # 5. Provider marks job Completed with realistic solution photo
        solution_bytes = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c434')
        res_job = self.client.post(f'/api/providers/jobs/{job_id}/status', data={
            'status': 'Completed',
            'notes': 'Replaced damaged 40A double-pole circuit breaker and verified load balance.',
            'resolution_proof': 'Voltage tested 120V steady across all phases.',
            'resolution_image': (io.BytesIO(solution_bytes), 'repaired_breaker.png')
        }, content_type='multipart/form-data')
        self.assertEqual(res_job.status_code, 200)

        # Verify job is resolved and has resolution_image_url
        with self.app.app_context():
            job = db.session.get(Job, job_id)
            self.assertEqual(job.status, 'Completed')
            self.assertIsNotNone(job.resolution_image_url)
            self.assertTrue(job.resolution_image_url.startswith('/static/uploads/'))
            self.assertEqual(job.complaint.status, 'Resolved')

    def test_05_admin_audit_resolutions_endpoint(self):
        # 6. Admin resolution audit shows problem, who solved it, and solution photo
        res_audit = self.client.get('/api/admin/audit-resolutions')
        self.assertEqual(res_audit.status_code, 200)
        audit_list = res_audit.get_json()
        self.assertIsInstance(audit_list, list)
        self.assertGreaterEqual(len(audit_list), 1)
        first = audit_list[0]
        self.assertIn('complaint_id', first)
        self.assertIn('title', first)
        self.assertIn('resolver_name', first)
        self.assertIn('resolution_image_url', first)


if __name__ == '__main__':
    unittest.main()
