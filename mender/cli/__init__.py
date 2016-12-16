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
import argparse

from mender.cli import deps, devadm, device, images, inventory, client, user
from mender.cli.utils import run_command, CommandNotSupportedError
from mender.client import ClientError

def parse_arguments():
    parser = argparse.ArgumentParser(description='mender backend client',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--debug', help='Enable debugging output',
                        default=False, action='store_true')
    parser.add_argument('-s', '--service', help='Service address',
                        default='https://docker.mender.io:8080/')
    parser.add_argument('-n', '--no-verify', help='Skip certificate verification',
                        default=False, action='store_true')
    parser.add_argument('--cacert', help='Server certificate for verification',
                        default='')
    parser.add_argument('-u', '--user-token', help='User token file',
                        default='usertoken')
    parser.set_defaults(command='')
    sub = parser.add_subparsers(help='Commands')

    pdeps = sub.add_parser('deployment', help='Deployments')
    deps.add_args(pdeps)
    pdeps.set_defaults(command='deployment')

    pim = sub.add_parser('image', help='Images')
    images.add_args(pim)
    pim.set_defaults(command='image')

    padm = sub.add_parser('admission', help='Admission')
    devadm.add_args(padm)
    padm.set_defaults(command='admission')

    pinv = sub.add_parser('inventory', help='Inventory')
    inventory.add_args(pinv)
    pinv.set_defaults(command='inventory')

    puse = sub.add_parser('user', help='User commands')
    user.add_args(puse)
    puse.set_defaults(command='user')

    pdev = sub.add_parser('device', help='Device')
    device.add_args(pdev)
    pdev.set_defaults(command='device')

    pclient = sub.add_parser('client', help='Simulate a mender client')
    client.add_args(pclient)
    pclient.set_defaults(command='client')

    return parser.parse_args()


def main():
    opts = parse_arguments()

    level = logging.INFO
    if opts.debug:
        level = logging.DEBUG

    logging.basicConfig(level=level)

    logging.debug('starting...')

    opts.verify = not opts.no_verify

    logging.debug('options: %r', opts)
    try:
        commands = {
            'deployment': deps.do_main,
            'admission': devadm.do_main,
            'device': device.do_main,
            'image': images.do_main,
            'inventory': inventory.do_main,
            'client':  client.do_main,
            'user':  user.do_main,
        }
        run_command(opts.command, commands, opts)
    except ClientError as rerr:
        logging.error('request failed: %s', rerr)
    except CommandNotSupportedError:
        logging.error('incomplete or unsupported command, see --help')
