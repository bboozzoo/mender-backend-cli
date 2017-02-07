# The MIT License (MIT)
#
# Copyright (c) 2016 Gregorio Di Stefano
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
import time
import threading
import os
import random
import tempfile
import copy
import sys

from mender.cli import device
import mender.cli.utils


def add_args(sub):
    sub.set_defaults(clientcommand='')

    sub.add_argument('-n', '--number', help="Number of clients", type=int, required=True)
    sub.add_argument('-i', '--inventory', help="Inventory items", action='append', default=["device_type:fake-device", "image_type:fake-image"])
    sub.add_argument('--inventory-update-freq', type=int, default=60)
    sub.add_argument('-w', '--wait', help="Maximum wait before changing update steps", type=int, default=30)
    sub.add_argument('-f', '--fail', help="Fail update with specific messsage", type=str, default="")
    sub.add_argument('-c', '--updates', help="Number of updates to perform before exiting", type=int, default=1)

def do_main(opts):
    threads = []

    client_options = []
    for _ in range(opts.number):
        new_opts = copy.deepcopy(opts)
        new_opts.store = True
        new_opts.verify = False
        new_opts.attrs_set = opts.inventory
        new_opts.mac_address = ":".join(["%02x" % random.randint(0x00, 0xFF) for i in range(6)])
        new_opts.device_key = tempfile.NamedTemporaryFile().name
        new_opts.tenant_token = tempfile.NamedTemporaryFile().name
        new_opts.device_token = tempfile.NamedTemporaryFile().name
        threads.append(threading.Thread(target=run_client, args=(new_opts,)))

    for t in threads:
        t.start()


def run_client(opts):
    logging.info("starting client with MAC: %s", opts.mac_address)
    block_until_authorized(opts)
    threading.Thread(target=send_inventory_data, args=(opts,)).start()

    if opts.updates:
        for _ in range(opts.updates):
            block_until_update(opts)
    else:
        while True:
            block_until_update(opts)

def block_until_authorized(opts):
    logging.info("performing bootstrap")
    device.do_key(opts)

    count = 1
    while True:
        if device.do_authorize(opts):
            logging.info("successfully bootstrapped client")
            return
        else:
            logging.info("device not authorized yet..")
            count += 1
            time.sleep(5)


def send_inventory_data(opts):
    while True:
        device.do_inventory(opts)
        time.sleep(opts.inventory_update_freq)


def block_until_update(opts):
    device.do_fake_update(opts)
