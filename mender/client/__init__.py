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
import logging

import requests
import requests.auth
from requests import Session as ApiClient


API_URL = '/api/integrations/0.1/'
API_DEVICES_URL = '/api/devices/0.1/'

def add_url_path(base, path):
    if not base.endswith('/'):
        base += '/'
    if path.startswith('/'):
        path = path[1:]
    return base + path


def service_path(service):
    return add_url_path(API_URL, service)


def admissions_url(host, path=''):
    ap = add_url_path(host, service_path('/admission/devices'))
    if path:
        return add_url_path(ap, path)
    return ap

def deployments_url(host, path=''):
    ap = add_url_path(host, service_path('/deployments/deployments'))
    if path:
        return add_url_path(ap, path)
    return ap

def images_url(host, path=''):
    ap = add_url_path(host, service_path('/deployments/images'))
    if path:
        return add_url_path(ap, path)
    return ap

def inventory_url(host, path=''):
    ap = add_url_path(host, service_path('/inventory'))
    if path:
        return add_url_path(ap, path)
    return ap

def device_url(host, path=''):
    ap = add_url_path(host, API_DEVICES_URL)
    if path:
        return add_url_path(ap, path)
    return ap


def user_url(host, path=''):
    ap = add_url_path(host, service_path('/useradm'))
    if path:
        return add_url_path(ap, path)
    return ap


class ClientError(requests.exceptions.RequestException):
    """Wrapper for client errors"""
    pass


class JWTAuth(requests.auth.AuthBase):
    """Perform device authentication using device token"""
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer {}'.format(self.token)
        return r
