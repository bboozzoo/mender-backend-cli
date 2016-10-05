import logging

import requests

from mender.cli.utils import run_command
from mender.client import deployments_url, do_simple_get


def add_args(sub):
    # deployments
    sub.set_defaults(depcommand='')

    pdsub = sub.add_subparsers(help='Commands for deployment')

    # deployment add
    pdadd = pdsub.add_parser('add', help='Add deployment')
    pdadd.set_defaults(depcommand='add')
    pdadd.add_argument('-a', '--artifact-name', help='Artifact name',
                       required=True)
    pdadd.add_argument('-e', '--device', help='Devices', action='append',
                       required=True)
    pdadd.add_argument('-n', '--name', help='Deployment name',
                       required=True)
    # deployment find
    pdfind = pdsub.add_parser('find', help='Lookup deployment')
    pdfind.set_defaults(depcommand='find')
    pdfind.add_argument('name', help='Deployment name')
    # deployment status
    pdstatus = pdsub.add_parser('status', help='See status')
    pdstatus.set_defaults(depcommand='status')
    pdstatus.add_argument('id', help='Deployment ID')
    # deployment statistics
    pdstats = pdsub.add_parser('stats', help='See statistics')
    pdstats.set_defaults(depcommand='stats')
    pdstats.add_argument('id', help='Deployment ID')
    # deployment devices
    pddevs = pdsub.add_parser('devices', help='List devices')
    pddevs.set_defaults(depcommand='devices')
    pddevs.add_argument('id', help='Deployment ID')
    # deployment device logs
    pdlogs = pdsub.add_parser('logs', help='Show device deployment logs')
    pdlogs.set_defaults(depcommand='logs')
    pdlogs.add_argument('id', help='Deployment ID')
    pdlogs.add_argument('devid', help='Device ID')


def do_main(opts):
    logging.debug('deployment opts: %r', opts)
    cmds = {
        'add': do_deployments_add,
        'devices': do_deployments_devices,
        'find': do_deployments_find,
        'logs': do_deployments_logs,
        'stats': do_deployments_stats,
        'status': do_deployments_status,
    }
    run_command(opts.depcommand, cmds, opts)


def do_deployments_find(opts):
    logging.debug('lookup deployment %s', opts.name)
    url = deployments_url(opts.service)
    do_simple_get(url, params={'name': opts.name},
                  verify=opts.verify)


def do_deployments_add(opts):
    logging.debug('lookup deployment %s', opts.name)
    url = deployments_url(opts.service)
    rsp = requests.post(url,
                        json={
                            'name': opts.name,
                            'artifact_name': opts.artifact_name,
                            'devices': opts.device,
                        },
                        verify=opts.verify)
    if rsp.status_code == 201:
        # created
        location = rsp.headers.get('Location', '')
        print("created with URL: {}".format(location))
        print('deployment ID: ', location.rsplit('/')[-1])
    else:
        logging.warning('request failed: %s %s', rsp, rsp.json())


def do_deployments_status(opts):
    logging.debug('get deployment %s', opts.id)
    url = deployments_url(opts.service, opts.id)
    do_simple_get(url, verify=opts.verify)


def do_deployments_stats(opts):
    logging.debug('get deployment %s stats', opts.id)
    url = deployments_url(opts.service, '{}/statistics'.format(opts.id))
    do_simple_get(url, verify=opts.verify)


def do_deployments_devices(opts):
    logging.debug('get deployment %s devices', opts.id)
    url = deployments_url(opts.service,
                          '{}/devices'.format(opts.id))
    do_simple_get(url, verify=opts.verify)


def do_deployments_logs(opts):
    logging.debug('get log for deployment %s on device %s', opts.id, opts.devid)
    url = deployments_url(opts.service,
                          '{}/devices/{}/log'.format(opts.id, opts.devid))
    do_simple_get(url, printer=simpleprinter, verify=opts.verify)
