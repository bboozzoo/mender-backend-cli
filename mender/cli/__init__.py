import logging
import argparse

from mender.cli import deps, devadm, device, images, inventory
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

    pdev = sub.add_parser('device', help='Device')
    device.add_args(pdev)
    pdev.set_defaults(command='device')

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
        }
        run_command(opts.command, commands, opts)
    except ClientError as rerr:
        logging.error('request failed: %s', rerr)
    except CommandNotSupportedError:
        logging.error('incomplete or unsupported command, see --help')


