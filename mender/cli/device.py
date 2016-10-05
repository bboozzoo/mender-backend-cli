import logging
import json
from base64 import b64encode, b64decode

import requests

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

from mender.cli.utils import run_command
from mender.client import device_url, do_simple_get, errorprinter, jsonprinter

def add_args(sub):
    pdev = sub.add_subparsers(help='Commands for device')
    sub.set_defaults(devcommand='')

    sub.add_argument('-k', '--device-key', help='Device key path',
                        default='key.priv')
    sub.add_argument('-o', '--device-token', default='devtoken', help='Device token path')

    pupdate = pdev.add_parser('update', help='Get update')
    pupdate.set_defaults(devcommand='update')

    pauthorize = pdev.add_parser('authorize', help='Authorize')
    pauthorize.add_argument('-s', '--seq-no', default=1, help='Sequence number')
    pauthorize.add_argument('-m', '--mac-address', default='de:ad:be:ef:00:01',
                            help='MAC address')
    pauthorize.add_argument('-t', '--tenant-token', default='dummy', help='Tenant token')
    pauthorize.set_defaults(devcommand='authorize')

    pkeys = pdev.add_parser('key', help='device key')
    pkeys.set_defaults(devcommand='key')

    ptoken = pdev.add_parser('token', help='device token')
    ptoken.set_defaults(devcommand='token')


def do_main(opts):
    commands = {
        'authorize': do_authorize,
        'key': do_key,
        'update': do_update,
        'token': do_token,
    }
    run_command(opts.devcommand, commands, opts)

def load_file(path):
    with open(path) as inf:
        data = inf.read()
    return data

def save_file(path, data):
    with open(path, 'wb') as outf:
        if isinstance(data, bytes):
            outf.write(data)
        else:
            outf.write(data.encode())

def gen_privkey():
    private = RSA.generate(1024)
    return private.exportKey()

def load_privkey(path):
    priv = load_file(path)
    return RSA.importKey(priv)

def sign(data, key):
    signer = PKCS1_v1_5.new(key)
    digest = SHA256.new()
    digest.update(data.encode())
    signed = signer.sign(digest)
    return b64encode(signed)

def do_authorize(opts):
    url = device_url(opts.service, '/authentication/auth_requests')

    try:
        key = load_privkey(opts.device_key)
    except IOError:
        logging.error('failed to load key from %s', opts.device_key)
        return

    identity = json.dumps({
        'mac': opts.mac_address,
    })
    logging.info('request sequence number %s', opts.seq_no)
    logging.debug('identity: %s', identity)
    data = json.dumps({
        'id_data': identity,
        'pubkey': str(key.publickey().exportKey(), 'utf-8'),
        'seq_no': int(opts.seq_no),
        'tenant_token': opts.tenant_token,
    })
    logging.debug('request data: %s', data)
    signature = sign(data, key)
    hdrs = {
        'X-MEN-Signature': signature,
        'Content-Type': 'application/json'
    }
    rsp = requests.post(url,
                        data=data,
                        headers=hdrs,
                        verify=opts.verify)

    if rsp.status_code == 200:
        logging.info('request successful')
        logging.info('token: %s', rsp.text)
        save_file(opts.device_token, rsp.text)
    else:
        logging.warning('request failed: %s %s', rsp, rsp.text)


def do_key(opts):
    logging.info('generating new key, writing to %s', opts.device_key)
    priv = gen_privkey()
    save_file(opts.device_key, priv)


def do_update(opts):
    def updateprinter(rsp):
        if rsp.status_code == 204:
            print('no update available')
        elif rsp.status_code == 200:
            jsonprinter(rsp)
        else:
            errorprinter(rsp)

    url = device_url(opts.service, '/deployments/device/update')
    token = load_file(opts.device_token)
    headers = headers={
        'Authorization': 'Bearer {}'.format(token),
    }
    logging.debug('with headers: %s', headers)
    do_simple_get(url, printer=updateprinter,
                  success=[200, 204],
                  headers=headers,
                  verify=opts.verify)


def pad_b64(b64s):
    pad = len(b64s) % 4
    if pad != 0:
        return b64s + '=' * pad
    return b64s

def do_token(opts):
    logging.info('show token')
    try:
        tok = load_file(opts.device_token)
    except IOError as err:
        logging.error('failed to load token from %s: %s',
                      opts.device_token, err)
        return

    split = tok.split('.')
    for name, val in zip(['type', 'claims'], split[0:2]):
        pad = pad_b64(val)
        logging.debug('padded: %s', pad)
        raw = b64decode(pad)
        # logging.info('%s: %s', n, raw)
        data = json.loads(str(raw, 'utf-8'))
        print('{}\n\t'.format(name), data)

    print('signature:\n\t', split[2])
