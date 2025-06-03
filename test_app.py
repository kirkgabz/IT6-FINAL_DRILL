import unittest
import json
from app import app

class TestAQIAPI(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        # Clear records before each test
        self.client.post('/api/records/reset')

    def test_create_record_success(self):
        data = {
            "pm25": 20.5,
            "pm10": 30.1,
            "o3": 15.2,
            "no2": 10.3,
            "co": 0.4,
            "so2": 5.0
        }
        response = self.client.post('/api/records', json=data)
        self.assertEqual(response.status_code, 201)
        resp_json = response.get_json()
        self.assertIn('id', resp_json)
        for key in data:
            self.assertEqual(resp_json[key], data[key])

    def test_create_record_invalid_data(self):
        # Missing fields
        data = {
            "pm25": "invalid",
            "pm10": 30.1
            # missing other fields
        }
        response = self.client.post('/api/records', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_get_records_empty(self):
        response = self.client.get('/api/records')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_get_single_record_success(self):
        # Create a record first
        data = {
            "pm25": 10,
            "pm10": 20,
            "o3": 5,
            "no2": 3,
            "co": 0.1,
            "so2": 1
        }
        post_resp = self.client.post('/api/records', json=data)
        record_id = post_resp.get_json()['id']

        get_resp = self.client.get(f'/api/records/{record_id}')
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.get_json()['id'], record_id)

    def test_get_single_record_not_found(self):
        get_resp = self.client.get('/api/records/nonexistent-id')
        self.assertEqual(get_resp.status_code, 404)
        self.assertIn('error', get_resp.get_json())

    def test_update_record_success(self):
        data = {
            "pm25": 10,
            "pm10": 20,
            "o3": 5,
            "no2": 3,
            "co": 0.1,
            "so2": 1
        }
        post_resp = self.client.post('/api/records', json=data)
        record_id = post_resp.get_json()['id']

        update_data = {
            "pm25": 25,
            "pm10": 35,
            "o3": 15,
            "no2": 8,
            "co": 0.5,
            "so2": 2
        }
        put_resp = self.client.put(f'/api/records/{record_id}', json=update_data)
        self.assertEqual(put_resp.status_code, 200)
        updated = put_resp.get_json()
        self.assertEqual(updated['pm25'], 25)
        self.assertEqual(updated['pm10'], 35)

    def test_update_record_invalid_data(self):
        data = {
            "pm25": 10,
            "pm10": 20,
            "o3": 5,
            "no2": 3,
            "co": 0.1,
            "so2": 1
        }
        post_resp = self.client.post('/api/records', json=data)
        record_id = post_resp.get_json()['id']

        invalid_data = {
            "pm25": "bad_value"
        }
        put_resp = self.client.put(f'/api/records/{record_id}', json=invalid_data)
        self.assertEqual(put_resp.status_code, 400)
        self.assertIn('error', put_resp.get_json())

    def test_update_record_not_found(self):
        update_data = {
            "pm25": 25,
            "pm10": 35,
            "o3": 15,
            "no2": 8,
            "co": 0.5,
            "so2": 2
        }
        put_resp = self.client.put('/api/records/nonexistent-id', json=update_data)
        self.assertEqual(put_resp.status_code, 404)
        self.assertIn('error', put_resp.get_json())

    def test_delete_record_success(self):
        data = {
            "pm25": 10,
            "pm10": 20,
            "o3": 5,
            "no2": 3,
            "co": 0.1,
            "so2": 1
        }
        post_resp = self.client.post('/api/records', json=data)
        record_id = post_resp.get_json()['id']

        del_resp = self.client.delete(f'/api/records/{record_id}')
        self.assertEqual(del_resp.status_code, 204)

        # Confirm deletion
        get_resp = self.client.get(f'/api/records/{record_id}')
        self.assertEqual(get_resp.status_code, 404)

    def test_delete_record_not_found(self):
        del_resp = self.client.delete('/api/records/nonexistent-id')
        self.assertEqual(del_resp.status_code, 404)
        self.assertIn('error', del_resp.get_json())

if __name__ == '__main__':
    unittest.main()
