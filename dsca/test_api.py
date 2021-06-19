from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from .models import LinkClickedEntry

# Create your tests here.

class LinkClickedEntryAPICreateTests(APITestCase):
    url = reverse('v1:linkclickedentry-api-create')

    @classmethod
    def setUp(self):
        self.test_data = [
            {},
            {
                'referer': 'https://g.com',
                'destination': 'https://a.com',
            }
        ]

    def test_create_new_valid_LinkClickedEntry(self):
        """
        Ensure we can cannot create a linkclickedentry object with no content.
        """
        response = self.client.post(self.url, self.test_data[0], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(LinkClickedEntry.objects.count(), 0)

    def test_create_valied_new_release(self):
        """
        Ensure we can create a basic linkclickedentry object
        """
        response = self.client.post(self.url, self.test_data[1], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LinkClickedEntry.objects.count(), 1)