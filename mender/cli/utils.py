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

import requests

from mender.client import ApiClient


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
