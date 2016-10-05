import logging
import io
from collections import OrderedDict

import requests

from mender.cli.utils import run_command
from mender.client import images_url, do_simple_get


def add_args(sub):
    pisub = sub.add_subparsers(help='Commands for images')
    sub.set_defaults(imcommand='')

    # image download
    pidown = pisub.add_parser('download', help='Download image')
    pidown.set_defaults(imcommand='download')
    pidown.add_argument('id', help='Image ID')
    # image remove
    pidel = pisub.add_parser('remove', help='Remove image')
    pidel.set_defaults(imcommand='remove')
    pidel.add_argument('id', help='Image ID')
    # image show
    pishow = pisub.add_parser('show', help='Show image')
    pishow.set_defaults(imcommand='show')
    pishow.add_argument('id', help='Image ID')
    # images list
    pishow = pisub.add_parser('list', help='List images')
    pishow.set_defaults(imcommand='list')
    # image add
    piadd = pisub.add_parser('add', help='Add image and upload its contents')
    piadd.set_defaults(imcommand='add')
    piadd.add_argument('-n', '--name', help='Image name', required=True)
    piadd.add_argument('-e', '--description', help='Image description', required=True)
    piadd.add_argument('-t', '--device-type', help='Device type', required=True)
    piadd.add_argument('-c', '--checksum', help='Image checksum', required=True)
    piadd.add_argument('-y', '--yocto-id', help='Yocto image name', required=True)
    piadd.add_argument('infile', help='Image file')

    piartifactadd = pisub.add_parser('add-artifact', help='Add image artifact and upload its contents')
    piartifactadd.set_defaults(imcommand='add-artifact')
    piartifactadd.add_argument('-n', '--name', help='Image name', required=True)
    piartifactadd.add_argument('-e', '--description', help='Image description', required=True)
    piartifactadd.add_argument('infile', help='Image file')


def do_main(opts):
    logging.debug('images opts: %r', opts)
    cmds = {
        'find': None,
        'list': do_images_list,
        'add': do_images_add,
        'add-artifact': do_images_artifact_add,
        'show': do_images_show,
        'remove': None,
        'download': do_images_download,
    }
    run_command(opts.imcommand, cmds, opts)


def do_images_add(opts):
    logging.debug('add image %r', opts)
    url = images_url(opts.service)
    image = {
        'name': opts.name,
        'description': opts.description,
        'device_type': opts.device_type,
        'yocto_id': opts.yocto_id,
        'checksum': opts.checksum,
    }
    # build contents of multipart/form-data, image meta must come first, hence
    # we use an OrderedDict to preserve the order
    files = OrderedDict()
    for k, v in image.items():
        files[k] = (None, io.StringIO(v))
    # followed by firmware data
    files['firmware'] = (opts.infile, open(opts.infile, 'rb'), "application/octet-stream", {})

    rsp = requests.post(url, files=files, verify=opts.verify)
    if rsp.status_code == 201:
        # created
        location = rsp.headers.get('Location', '')
        print("created with URL: {}".format(location))
        print('image ID: ', location.rsplit('/')[-1])
    else:
        logging.warning('request failed: %s %s', rsp, rsp.json())


def do_images_artifact_add(opts):
    logging.debug('add image artifact %r', opts)
    url = images_url(opts.service)
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
    files['firmware'] = (opts.infile, open(opts.infile, 'rb'), "application/octet-stream", {})

    rsp = requests.post(url, files=files, verify=opts.verify)
    if rsp.status_code == 201:
        # created
        location = rsp.headers.get('Location', '')
        print("created with URL: {}".format(location))
        print('image ID: ', location.rsplit('/')[-1])
    else:
        logging.warning('request failed: %s %s', rsp, rsp.json())


def do_images_download(opts):
    logging.debug('get image %s download', opts.id)
    url = images_url(opts.service, '/{}/download'.format(opts.id))

    do_simple_get(url, verify=opts.verify)


def do_images_show(opts):
    logging.debug('get image %s download', opts.id)
    url = images_url(opts.service, opts.id)
    do_simple_get(url, verify=opts.verify)


def do_images_list(opts):
    logging.debug('list images')
    url = images_url(opts.service)
    do_simple_get(url, verify=opts.verify)
