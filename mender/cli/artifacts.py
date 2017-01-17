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
import io
import os
import sys
from collections import OrderedDict

import requests
from requests_toolbelt import MultipartEncoder

from mender.cli.utils import run_command, do_simple_get, api_from_opts, errorprinter
from mender.client import artifacts_url


def add_args(sub):
    pisub = sub.add_subparsers(help='Commands for artifacts')
    sub.set_defaults(artcommand='')

    # artifact download
    pidown = pisub.add_parser('download', help='Download artifact')
    pidown.set_defaults(artcommand='download')
    pidown.add_argument('id', help='Image ID')
    # artifact remove
    pidel = pisub.add_parser('remove', help='Remove artifact')
    pidel.set_defaults(artcommand='remove')
    pidel.add_argument('id', help='Image ID')
    # artifact show
    pishow = pisub.add_parser('show', help='Show artifact')
    pishow.set_defaults(artcommand='show')
    pishow.add_argument('id', help='Image ID')
    # artifacts list
    pishow = pisub.add_parser('list', help='List artifacts')
    pishow.set_defaults(artcommand='list')
    # artifact add
    piartifactadd = pisub.add_parser('add', help='Add artifact')
    piartifactadd.set_defaults(artcommand='add')
    piartifactadd.add_argument('-n', '--name', help='Artifact name', required=True)
    piartifactadd.add_argument('-e', '--description', help='Artifact description', required=True)
    piartifactadd.add_argument('infile', help='Artifact file')


def do_main(opts):
    logging.debug('artifacts opts: %r', opts)
    cmds = {
        'find': None,
        'list': do_artifacts_list,
        'add': do_artifacts_artifact_add,
        'show': do_artifacts_show,
        'remove': None,
        'download': do_artifacts_download,
    }
    run_command(opts.artcommand, cmds, opts)


def do_artifacts_artifact_add(opts):
    logging.debug('add artifact %r', opts)
    url = artifacts_url(opts.service)
    image = {
        'name': opts.name,
        'description': opts.description,
    }
    # build contents of multipart/form-data, image meta must come first, hence
    # we use an OrderedDict to preserve the order
    files = OrderedDict()
    for k, v in image.items():
        files[k] = (None, io.StringIO(v))
    # followed by firmware data
    # but first, try to find out the size of firmware data
    sz = os.stat(opts.infile).st_size
    files['artifact'] = (opts.infile, open(opts.infile, 'rb'), "application/octet-stream", {})

    encoder = MultipartEncoder(files)

    if sys.stderr.isatty():
        try:
            from requests_toolbelt import MultipartEncoderMonitor
            from clint.textui.progress import Bar as ProgressBar

            pb = ProgressBar(expected_size=encoder.len, filled_char='=', every=1024*1024)
            monitor = MultipartEncoderMonitor(encoder,
                                              lambda mon: pb.show(mon.bytes_read))
            encoder = monitor
        except ImportError:
            pass

    with api_from_opts(opts) as api:
        rsp = api.post(url, data=encoder,
                       headers={'Content-Type': encoder.content_type})
        if rsp.status_code == 201:
            # created
            location = rsp.headers.get('Location', '')
            print("created with URL: {}".format(location))
            print('artifact ID: ', location.rsplit('/')[-1])
        else:
            errorprinter(rsp)


def do_artifacts_download(opts):
    logging.debug('get artifact %s download', opts.id)
    url = artifacts_url(opts.service, '/{}/download'.format(opts.id))

    with api_from_opts(opts) as api:
        do_simple_get(api, url)


def do_artifacts_show(opts):
    logging.debug('get artifact %s download', opts.id)
    url = artifacts_url(opts.service, opts.id)
    with api_from_opts(opts) as api:
        do_simple_get(api, url)


def do_artifacts_list(opts):
    logging.debug('list artifacts')
    url = artifacts_url(opts.service)
    with api_from_opts(opts) as api:
        do_simple_get(api, url)
