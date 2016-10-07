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

from mender.cli.utils import run_command
from mender.client import admissions_url, do_request, do_simple_get


def add_args(sub):
    padm = sub.add_subparsers(help='Commands for admissions')
    sub.set_defaults(admcommand='')

    paccept = padm.add_parser('accept', help='Accept device')
    paccept.add_argument('device', help='Device ID')
    paccept.set_defaults(admcommand='accept')

    preject = padm.add_parser('reject', help='Reject device')
    preject.add_argument('device', help='Device ID')
    preject.set_defaults(admcommand='reject')

    pshow = padm.add_parser('show', help='Show device')
    pshow.add_argument('device', help='Device ID')
    pshow.set_defaults(admcommand='show')

    plist = padm.add_parser('list', help='List devices')
    plist.set_defaults(admcommand='list')


def do_main(opts):
    commands = {
        'list': list_devices,
        'accept': lambda o: set_device_status(o, 'accepted'),
        'reject': lambda o: set_device_status(o, 'rejected'),
        'show': show_device,
    }
    run_command(opts.admcommand, commands, opts)


def dump_device(data, showkey=True):
    logging.debug('device data: %r', data)
    print('device: %s' % data['id'])
    print('    status: %s' % data['status'])
    print('    request time: %s' % data['request_time'])
    print('    attributes:')
    for key, val in data['attributes'].items():
        print('        %s : %s' % (key, val))
    if showkey:
        print('    public key:')
        print(data['key'])


def show_device(opts):
    url = admissions_url(opts.service, '/{}'.format(opts.device))
    rsp = do_simple_get(url,
                        printer=lambda rsp: dump_device(rsp.json()),
                        verify=opts.verify)


def list_devices(opts):
    do_simple_get(admissions_url(opts.service),
                  printer=lambda rsp: [dump_device(dev,
                                                   showkey=False)
                                       for dev in rsp.json()],
                  verify=opts.verify)


def set_device_status(opts, status):
    url = admissions_url(opts.service, '/{}/status'.format(opts.device))
    logging.debug('device URL: %s', url)
    do_request(url, method='PUT',
               verify=opts.verify,
               json={
                   'status': status
               })
