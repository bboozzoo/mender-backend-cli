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
import json
import os.path
from base64 import b64decode

import requests

from mender.client import ApiClient, JWTAuth


def run_command(command, cmds, opts):
    '''Locate and call `command` handler in a map `cmds`. The handler is called
    with `opts` as its first argument.

    Will raise CommandNotSupport(command) if command is not found.

    :param command: command as string
    :param cmds: map of commands, command name being the key, a function being the value
    :type cmds: map
    :param opts: options passed to command handler

    '''
    handler = cmds.get(command, None)
    if not handler:
        raise CommandNotSupportedError(command)
    else:
        handler(opts)


class CommandNotSupportedError(Exception):
    """Indicates that `command` is not supported"""
    def __init__(self, command):
        super().__init__(command)
        self.command = command
    def __str__(self):
        return 'command {} is not supported'.format(self.command)


def api_from_opts(opts):
    api = ApiClient()
    if opts.no_verify:
        api.verify = False
    if opts.cacert:
        api.verify = opts.cacert
    if opts.user_token and os.path.exists(opts.user_token):
        logging.info('loading user token from %s', opts.user_token)
        token = load_file(opts.user_token)
        api.auth = JWTAuth(token)
    return api

def jsonprinter(rsp):
    """Printer for JSON type responses"""
    from pprint import pprint
    if not isinstance(rsp, requests.Response):
        raise TypeError("expected requests.Response")
    try:
        pprint(rsp.json())
    except ValueError:
        logging.error("Failed to pprint response, content was not JSON")
        logging.error("response text: %s", rsp.text)


def simpleprinter(rsp):
    """Printer for text type responses"""
    if not isinstance(rsp, requests.Response):
        raise TypeError("expected requests.Response")
    print(rsp.text)


def errorprinter(rsp):
    """Helper printer for error responses"""
    try:
        dec = json.loads(rsp.text)
    except ValueError:
        logging.debug('not a JSON response, got %s instead',
                      rsp.headers.get('Content-Type', 'Content-Type unset'))
        dec = rsp.text
    finally:
        logging.warning('request failed: %s %s', rsp, rsp.text)


def do_simple_get(api, url, printer=jsonprinter, success=200, **kwargs):
    return do_request(api, url, method='GET',
                      printer=printer, success=success, **kwargs)


def do_request(api, url, method='GET', printer=jsonprinter, success=[200, 204], **kwargs):
    rsp = api.request(method, url, **kwargs)
    logging.debug(rsp)
    if (isinstance(success, list) and rsp.status_code in success) \
       or rsp.status_code == success:
        if rsp.status_code != 204 and printer:
            if len(rsp.content) > 1024 * 1024:
                logging.info("response too big to print")
            else:
                printer(rsp)
    else:
        errorprinter(rsp)
    return rsp


def pad_b64(b64s):
    """Pad Base64 encoded string so that its length is a multiple of 4 bytes"""
    pad = len(b64s) % 4
    if pad != 0:
        return b64s + '=' * pad
    return b64s


def dump_token(tok):
    split = tok.split('.')
    for name, val in zip(['type', 'claims'], split[0:2]):
        pad = pad_b64(val)
        logging.debug('padded: %s', pad)
        raw = b64decode(pad)
        # logging.info('%s: %s', n, raw)
        data = json.loads(str(raw, 'utf-8'))
        print('{}\n\t'.format(name), data)

    print('signature:\n\t', split[2])


def load_file(path):
    """Load contents of a file"""
    with open(path) as inf:
        data = inf.read()
    return data


def save_file(path, data):
    """Save data to file"""
    with open(path, 'wb') as outf:
        if isinstance(data, bytes):
            outf.write(data)
        else:
            outf.write(data.encode())
