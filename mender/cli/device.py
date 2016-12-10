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
import time
import random
import tempfile
import os
from base64 import b64encode, b64decode

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

import requests

from mender.cli.utils import run_command, api_from_opts, do_simple_get, do_request, \
    errorprinter, jsonprinter
from mender.client import device_url, DeviceTokenAuth

def add_args(sub):
    pdev = sub.add_subparsers(help='Commands for device')
    sub.set_defaults(devcommand='')

    sub.add_argument('-k', '--device-key', help='Device key path',
                     default='key.priv')
    sub.add_argument('-o', '--device-token', default='devtoken', help='Device token path')

    pupdate = pdev.add_parser('update', help='Get update')
    pupdate.set_defaults(devcommand='update')

    pdevattr = pdev.add_parser('inventory', help='Send device attributes')
    pdevattr.add_argument('-s', '--attrs-set',
                          help='Assign attributes, format <name>:<value>, specify multiple times',
                          action='append', required=True)
    pdevattr.set_defaults(devcommand='inventory')

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

    pfake_update = pdev.add_parser('fake-update',
                                   help='Perform fake upgrade by going through: update check - download - report loop')
    pfake_update.add_argument('-f', '--fail', default='',
                              help='Report update failure with this message')
    pfake_update.add_argument('-w', '--wait', default=30,
                              help='Maximum amount of time to wait between updating deployment status')
    pfake_update.add_argument('-s', '--store', action='store_true',
                              help='Store the image downloaded')
    pfake_update.set_defaults(devcommand='fake-update')

def do_main(opts):
    commands = {
        'authorize': do_authorize,
        'key': do_key,
        'update': do_update,
        'token': do_token,
        'inventory': do_inventory,
        'fake-update': do_fake_update
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

def download_image(url, deployment_id, store=False, **kwargs):
    rsp = do_simple_get(url, stream=True, **kwargs)
    logging.debug('status %s', rsp.status_code)
    if rsp.status_code == 200:
        if store:
            with tempfile.NamedTemporaryFile(prefix=deployment_id[0:8], dir=os.getcwd()) as f:
                for chunk in rsp.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
    else:
        logging.error('failed to download image from %s: %s', url, rsp.text)

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
    with api_from_opts(opts) as api:
        rsp = api.post(url,
                       data=data,
                       headers=hdrs)

        if rsp.status_code == 200:
            logging.info('request successful')
            logging.info('token: %s', rsp.text)
            save_file(opts.device_token, rsp.text)
            return True
        else:
            logging.warning('request failed: %s %s', rsp, rsp.text)
    return False


def do_key(opts):
    logging.info('generating new key, writing to %s', opts.device_key)
    priv = gen_privkey()
    save_file(opts.device_key, priv)


def do_inventory(opts):
    url = device_url(opts.service, '/inventory/device/attributes')

    # prepare attributes
    attrs = []
    for attr in opts.attrs_set:
        n, v = attr.split(':')
        attrs.append({'name': n.strip(), 'value': v.strip()})

    with device_api_from_opts(opts) as api:
        do_request(api, url, method='PATCH', json=attrs)


def do_update(opts):
    def updateprinter(rsp):
        if rsp.status_code == 204:
            print('no update available')
        elif rsp.status_code == 200:
            jsonprinter(rsp)
        else:
            errorprinter(rsp)

    url = device_url(opts.service, '/deployments/device/update')
    with device_api_from_opts(opts) as api:
        return do_simple_get(api, url, printer=updateprinter,
                             success=[200, 204])

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

def do_fake_update(opts):
    logging.info('fake update')
    while True:
        resp = do_update(opts)
        if resp.status_code == 200:
            break
        else:
            logging.info("No update available..")
        time.sleep(5)

    deployment_id = resp.json()["id"]
    deployment_image_uri = resp.json()["image"]["uri"]

    logging.info("Update: " + deployment_id + " available")

    url = device_url(opts.service,
                     '/deployments/device/deployments/%s/status' % deployment_id)

    with device_api_from_opts(opts) as api:
        do_request(api, url, method='PUT', json={"status": "installing"})

        download_image(deployment_image_uri,
                       deployment_id=deployment_id, store=opts.store)

        do_request(api, url, method='PUT', json={"status": "downloading"})
        time.sleep(random.randint(0, int(opts.wait)))

        do_request(api, url, method='PUT', json={"status": "rebooting"})
        time.sleep(random.randint(0, int(opts.wait)))

        if opts.fail:
            do_request(api, url, method='PUT', json={"status": "failure"})
            logsurl = device_url(opts.service,
                                 '/deployments/device/deployments/%s/log' % deployment_id)
            do_request(api, logsurl, method='PUT',
                       json={
                           "messages": [
                               {
                                   "level": "debug",
                                   "message": opts.fail,
                                   "timestamp": "2012-11-01T22:08:41+00:00"
                               }
                           ]
                       })
        else:
            do_request(api, url, method='PUT',
                       json={"status": "success"})


def device_api_from_opts(opts):
    api = api_from_opts(opts)

    if os.path.exists(opts.device_token):
        token = load_file(opts.device_token)
        api.auth = DeviceTokenAuth(token)

    return api
