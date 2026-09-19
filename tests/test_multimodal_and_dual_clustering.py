import os
import sys
import io
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import create_app
from backend.models import Complaint, User, Provider
from database.db import db


class TestMultimodalAndDualClustering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_multimodal_complaint_creation_with_image_and_voice(self):
        # Using bytes.fromhex to avoid null byte in python source code
        image_bytes = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c434')
        data = {
            'title': 'Severe Sparking Electrical Box in Library',
            'description': 'Reported via voice: The main junction box is throwing dangerous electrical sparks near aisle 4.',
            'building': 'Central Library',
            'room_or_area': 'L-204',
            'is_voice_input': 'true',
            'student_id': 1,
            'image': (io.BytesIO(image_bytes), 'incident_spark.png')
        }

        response = self.client.post(
            '/api/complaints',
            data=data,
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 201)
        res_json = response.get_json()
        self.assertIn('complaint', res_json)
        complaint_data = res_json['complaint']
        
        self.assertTrue(complaint_data.get('is_voice_input'))
        self.assertIsNotNone(complaint_data.get('image_url'))
        self.assertTrue(complaint_data['image_url'].startswith('/static/uploads/'))

        with self.app.app_context():
            saved_c = db.session.get(Complaint, complaint_data['id'])
            self.assertIsNotNone(saved_c)
            self.assertTrue(saved_c.is_voice_input)
            self.assertIsNotNone(saved_c.image_url)

    def test_dual_basis_clustering_endpoints(self):
        # Test 1: basis=volume
        res_vol = self.client.get('/api/admin/clusters?basis=volume')
        self.assertEqual(res_vol.status_code, 200)
        vol_data = res_vol.get_json()
        self.assertEqual(vol_data.get('basis'), 'volume')
        self.assertIn('clusters', vol_data)

        # Test 2: basis=severity
        res_sev = self.client.get('/api/admin/clusters?basis=severity')
        self.assertEqual(res_sev.status_code, 200)
        sev_data = res_sev.get_json()
        self.assertEqual(sev_data.get('basis'), 'severity')
        self.assertIn('clusters', sev_data)
        self.assertGreaterEqual(len(sev_data['clusters']), 1)
        # Verify severity fields in cluster items
        first_cluster = sev_data['clusters'][0]
        self.assertIn('hazard_score', first_cluster)
        self.assertIn('severity_label', first_cluster)

        # Test 3: trigger run-dbscan with basis=severity
        res_run = self.client.post(
            '/api/admin/clusters/run-dbscan',
            json={'basis': 'severity'}
        )
        self.assertEqual(res_run.status_code, 200)
        run_data = res_run.get_json()
        self.assertEqual(run_data.get('basis'), 'severity')

    def test_admin_directory_endpoint(self):
        res = self.client.get('/api/admin/directory')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        # Directory returns a list of user/provider/admin dicts
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        # Verify student and provider presence
        roles = {member.get('role') for member in data}
        self.assertIn('student', roles)
        self.assertIn('provider', roles)
        self.assertIn('admin', roles)


if __name__ == '__main__':
    unittest.main()
