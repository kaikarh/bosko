from django.test import TestCase

from .models import Release

from .postautomation import validity_check

class ValidityCheckTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dummy_objects = [
            {
                'release_name': 'something_that_cant_be_parsed',
                'archive_name': '0.zip',
            },
            {
                'release_name': 'Cousin_Feo_x_Bohemia_Lynch-Yakitori-EP-WEB-2021-UVU',
                'archive_name': '1.zip',
            },
            {
                'release_name': 'Hillsburn-Slipping_Away-WEB-2021-SOMEFICTIONARYGROUP',
                'archive_name': '3.zip',
            },
            {
                'release_name': 'ROSE-R-WEB-KR-2021-HUNNiT',
                'archive_name': '3.zip',
            },
            {
                'release_name': 'Someotherartist-Someotheralbum-WEB-2021-SOMEFICTIONARYGROUP',
                'archive_name': '4.zip',
                'adam_id': '',
            },
            {
                'release_name': 'Hillsburn-Slipping_Away-(LHM021)-CD-2021-VULGAR',
                'archive_name': '2.zip',
                'adam_id': '1565817538',
                'posted': True,
            },
        ]

        cls.test_objects = []
        for obj in dummy_objects:
            o = Release.objects.create(**obj)
            cls.test_objects.append(o)

    def test_name_not_parsable(self):
        with self.assertRaisesMessage(Exception, 'Not found'):
            validity_check(self.test_objects[0])

    def test_no_match_found(self):
        with self.assertRaisesMessage(Exception, 'Not found'):
            validity_check(self.test_objects[1])

    def test_duplicate(self):
        with self.assertRaisesMessage(Exception, 'Duplication'):
            validity_check(self.test_objects[2])

    def test_invalid_match(self):
        with self.assertRaisesMessage(Exception, 'Search Result Validation Failed'):
            validity_check(self.test_objects[3])