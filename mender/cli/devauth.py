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
from mender.cli.utils import run_command, api_from_opts, do_simple_get
from mender.client import authentication_url


def add_args(sub):
    pauth = sub.add_subparsers(help='Commands for device authentication')
    sub.set_defaults(authcommand='')

    pshow = pauth.add_parser('show', help='Show device')
    pshow.add_argument('device', help='Device ID')
    pshow.set_defaults(authcommand='show')

    plist = pauth.add_parser('list', help='List devices')
    plist.set_defaults(authcommand='list')


def do_main(opts):
    commands = {
        'list': list_devices,
        'show': show_device,
    }
    run_command(opts.authcommand, commands, opts)


def show_device(opts):
    url = authentication_url(opts.service, '/devices/{}'.format(opts.device))
    with api_from_opts(opts) as api:
        rsp = do_simple_get(api, url)


def list_devices(opts):
    with api_from_opts(opts) as api:
        do_simple_get(api, authentication_url(opts.service, '/devices'))
