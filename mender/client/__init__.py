import logging
import json

import requests

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


class ClientError(requests.exceptions.RequestException):
    """Wrapper for client errors"""
    pass


def jsonprinter(rsp):
    """Printer for JSON type responses"""
    from pprint import pprint
    if not isinstance(rsp, requests.Response):
        raise TypeError("expected requests.Response")
    pprint(rsp.json())


def simpleprinter(rsp):
    """Printer for text type responses"""
    if not isinstance(rsp, requests.Response):
        raise TypeError("expected requests.Response")
    print(rsp.text)

def errorprinter(rsp):
    """Helper printer for error responses"""
    try:
        dec = json.loads(rsp.text)
    except json.JSONDecodeError:
        logging.debug('not a JSON response, got %s instead',
                      rsp.headers.get('Content-Type', 'Content-Type unset'))
        dec = rsp.text
    finally:
        logging.warning('request failed: %s %s', rsp, dec)


def do_simple_get(url, printer=jsonprinter, success=200, **kwargs):
    return do_request(url, method='GET',
                      printer=printer, success=success, **kwargs)


def do_request(url, method='GET', printer=jsonprinter, success=200, **kwargs):
    rsp = requests.request(method, url, **kwargs)
    logging.debug(rsp)
    if (isinstance(success, list) and rsp.status_code in success) \
       or rsp.status_code == success:
        if rsp.status_code != 204 and printer:
            printer(rsp)
    else:
        errorprinter(rsp)
    return rsp
