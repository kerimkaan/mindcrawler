import unittest
import random
from app import factory, r

class TestApp(unittest.TestCase):
    def test_create_link(self):
        with factory.test_client() as client:
            print('Create Service Tests')

            # create a link with already exists correct data
            response = client.post('/create', json={'url': 'https://www.google.com'})
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json['success'], False)
            self.assertEqual(response.json['message'], 'Link already exist')
            print('✓ Conflict (409) Test Passed') 

            # create a link with missing data
            response = client.post('/create', json={})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json['success'], False)
            self.assertEqual(response.json['message'], 'Missing JSON in request')
            print('✓ Bad Request (400) with Missing Data Test Passed')

            # create a link with empty data
            response = client.post('/create', json={'url': ''})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json['success'], False)
            self.assertEqual(response.json['message'], 'Scheme or url is missing, you can add it to your link like https://google.com')
            print('✓ Bad Request (400) with Empty Data Test Passed')

            # create a link with missing scheme in the url
            response = client.post('/create', json={'url': 'google.com'})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json['success'], False)
            self.assertEqual(response.json['message'], 'Scheme or url is missing, you can add it to your link like https://google.com')
            print('✓ Bad Request (400) with Missing Scheme Test Passed')

            # create a link is accepted (202) for processing
            response = client.post('/create', json={'url': 'https://example.com'}) # example.com is skipped in the worker
            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.json['success'], False)
            self.assertEqual(response.json['message'], 'Link is processing')
            print('✓ Accepted (202) Test Passed')

            # create a link with correct data
            randomUrl = 'https://' + str(random.randint(0, 1000000)) + '.com'
            response = client.post('/create', json={'url': randomUrl})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['success'], True)
            self.assertEqual(response.json['message'], 'Link created successfully')
            r.delete('url:' + randomUrl.split('://')[1]) # delete the link from redis
            print('✓ Success (200) Test Passed')

    def test_get_result(self):
        with factory.test_client() as client:
            print('Get Result Service Tests')

            # get result for an existing link
            response = client.get('/result?url=https://www.google.com')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['success'], True)
            self.assertEqual(response.json['message'], 'Link found')
            self.assertIn('title', response.json['result'])
            self.assertIn('description', response.json['result'])
            self.assertIn('status', response.json['result'])
            self.assertIn('createdAt', response.json['result'])
            self.assertIn('took', response.json['result'])
            print('✓ Success (200) Test Passed')

            # get result for a non-existing link
            response = client.get('/result?url=https://www.nonexistingurl.com')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json['success'], False)
            self.assertEqual(response.json['message'], 'Link not found')
            print('✓ Not Found (404) Test Passed')

            # get result for a link with missing data
            response = client.get('/result')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json['success'], False)
            self.assertEqual(response.json['message'], 'Missing URL in request')
            print('✓ Bad Request (400) with Missing Data Test Passed')

            # get result for a link with empty data
            response = client.get('/result?url=')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json['success'], False)
            self.assertEqual(response.json['message'], 'Missing URL in request')
            print('✓ Bad Request (400) with Empty Data Test Passed')

if __name__ == '__main__':
    unittest.main()
