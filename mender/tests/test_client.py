import unittest
import mock

from mender import client

class UrlsTestCase(unittest.TestCase):

    def test_add_url_path(self):

        self.assertEqual(client.add_url_path('foo', 'bar'),
                         'foo/bar')
        self.assertEqual(client.add_url_path('foo/', 'bar'),
                         'foo/bar')
        self.assertEqual(client.add_url_path('foo/', '/bar'),
                         'foo/bar')
        self.assertEqual(client.add_url_path('foo', '/bar'),
                         'foo/bar')

    def test_service_path(self):
        p = client.service_path('/foo/bar')
        self.assertEqual(p, '/api/integrations/0.1/foo/bar')

    def test_urls(self):
        aurl = client.admissions_url('http://foo:123/')
        self.assertEqual(aurl, 'http://foo:123/api/integrations/0.1/admission/devices')

        aurl = client.admissions_url('http://foo:123')
        self.assertEqual(aurl, 'http://foo:123/api/integrations/0.1/admission/devices')

        aurl = client.admissions_url('http://foo:123', '/foobar')
        self.assertEqual(aurl, 'http://foo:123/api/integrations/0.1/admission/devices/foobar')
