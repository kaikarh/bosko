from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from .api.views import ReleaseAPIViewSet
from .models import Release

# Create your tests here.

class ReleaseAPICreateTests(APITestCase):
    url = url = reverse('v1:release-list')

    def test_create_new_release_without_links(self):
        """
        Ensure we can cannot create a release object with no links.
        """
        data = {'release_name': 'Artist-Title-2021-grpname', 'archive_name': 'arc.zip', 'link_set': ''}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Release.objects.count(), 0)

    def test_create_valied_new_release(self):
        """
        Ensure we can create a basic release object
        """
        data = {
            'release_name': 'Artist-Title-2021-grpname',
            'archive_name': 'arc.zip',
            'link_set': [
                {'url': 'https://www.google.com/', 'passcode': '1234'},
                {'url': 'https://www.youtube.com/',}
            ]
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Release.objects.count(), 1)
        self.assertEqual(Release.objects.get().release_name, data['release_name'])
        self.assertEqual(Release.objects.get().archive_name, data['archive_name'])
        self.assertTrue(Release.objects.get().link_set.get(url=data['link_set'][0]['url']))
        self.assertTrue(Release.objects.get().link_set.get(url=data['link_set'][1]['url']))
