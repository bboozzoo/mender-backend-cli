# The MIT License (MIT)
#
# Copyright (c) 2016 Maciej Borzecki
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
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
