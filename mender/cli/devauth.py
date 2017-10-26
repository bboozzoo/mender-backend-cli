# The MIT License (MIT)
#
# Copyright (c) 2017 Maciej Borzecki
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

from mender.cli.utils import run_command, api_from_opts, do_simple_get, do_simple_delete
from mender.client import authentication_url


def add_args(sub):
    pauth = sub.add_subparsers(help='Commands for device authentication')
    sub.set_defaults(authcommand='')

    pshow = pauth.add_parser('show', help='Show device')
    pshow.add_argument('device', help='Device ID')
    pshow.set_defaults(authcommand='show')

    plist = pauth.add_parser('list', help='List devices')
    plist.set_defaults(authcommand='list')

    pcount = pauth.add_parser('count', help='Count devices with given status')
    pcount.add_argument('status', help='device status (pending|accepted|rejected)')
    pcount.set_defaults(authcommand='count')

    pdelete = pauth.add_parser('delete', help='Delete device')
    pdelete.add_argument('device', help='Device ID')
    pdelete.set_defaults(authcommand='delete')


def do_main(opts):
    commands = {
        'list': list_devices,
        'count': count_devices,
        'show': show_device,
        'delete': delete_device,
    }
    run_command(opts.authcommand, commands, opts)


def dump_device_brief(data):
    logging.debug('device auth data: %r', data)
    print('device ID: %s' % data['id'])
    print('    created:  %s' % data['created_ts'])
    print('    auth sets: %s' % ', '.join(['{} ({})'.format(aset['id'], aset['status'])
                                           for aset in
                                           data.get('auth_sets', [])]))

def dump_device(data):
    logging.debug('device auth data: %r', data)
    print('device ID: %s' % data['id'])
    print('    created:  %s' % data['created_ts'])
    print('    auth sets:')
    for aset in data.get('auth_sets', []):
        print('       id: %s' % aset['id'])
        print('       status: %s' % aset['status'])
        print('       identity data: %s' % aset['id_data'])
        key_lines = aset['pubkey'].split('\n')
        print('       key:', key_lines[0])
        for l in key_lines[1:]:
            print(' ' * 11, l)


def show_device(opts):
    url = authentication_url(opts.service, '/devices/{}'.format(opts.device))
    with api_from_opts(opts) as api:
        rsp = do_simple_get(api, url,
                            printer=lambda rsp: dump_device(rsp.json()))


def list_devices(opts):
    with api_from_opts(opts) as api:
        do_simple_get(api, authentication_url(opts.service, '/devices'),
                      printer=lambda rsp: [dump_device_brief(dev)
                                           for dev in rsp.json()])

def delete_device(opts):
    url = authentication_url(opts.service, '/devices/{}'.format(opts.device))
    with api_from_opts(opts) as api:
        rsp = do_simple_delete(api, url)

def count_devices(opts):
    url = authentication_url(opts.service, '/devices/count?{}'.format(opts.status))
    with api_from_opts(opts) as api:
        rsp = do_simple_get(api, url)
