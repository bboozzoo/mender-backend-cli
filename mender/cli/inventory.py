import logging

import requests

from mender.cli.utils import run_command
from mender.client import inventory_url, do_simple_get, do_request, errorprinter


def add_args(sub):
    pinvsub = sub.add_subparsers(help='Commands for inventory')
    sub.set_defaults(invcommand='')

    pdev = pinvsub.add_parser('device', help='Device commands')
    pdev.set_defaults(invcommand='device')

    pdevsub = pdev.add_subparsers(help='Device commands')

    pdev = pdevsub.add_parser('show', help='Show device')
    pdev.add_argument('device', help='Device ID')
    pdev.set_defaults(invdevcommand='show')

    pdevgroup = pdevsub.add_parser('group', help='Show/change device group assignment')
    pdevgroup.add_argument('device', help='Device ID')
    pdevgroup.add_argument('-s', '--group-set', help='Assign to group')
    pdevgroup.add_argument('-d', '--group-delete', help='Delete group')
    pdevgroup.set_defaults(invdevcommand='group')

    pdevlist = pdevsub.add_parser('list', help='List devices')
    pdevlist.set_defaults(invdevcommand='list')

    pdevattr = pdevsub.add_parser('attrs', help='Show/set device attributes')
    pdevattr.add_argument('device', help='Device ID')
    pdevattr.add_argument('-s', '--attrs-set',
                          help='Assign attributes, format <name>:<value>, specify multiple times',
                          action='append')
    pdevattr.set_defaults(invdevcommand='attrs')

    pgr = pinvsub.add_parser('group', help='Group commands')
    pgr.set_defaults(invcommand='group')

    pgrsub = pgr.add_subparsers(help='Group commands')

    pglist = pgrsub.add_parser('list', help='List groups')
    pglist.set_defaults(invgrcommand='list')

    pg = pgrsub.add_parser('show', help='Show group devices')
    pg.add_argument('group', help='Group ID')
    pg.set_defaults(invgrcommand='show')


def do_main(opts):
    commands = {
        'group': do_group,
        'device': do_device,
    }
    run_command(opts.invcommand, commands, opts)


def do_device(opts):
    commands = {
        'show': device_show,
        'group': device_group,
        'attrs': device_attrs,
        'list': devices_list,
    }
    run_command(opts.invdevcommand, commands, opts)


def do_group(opts):
    commands = {
        'list': group_list,
        'show': group_show,
    }
    run_command(opts.invgrcommand, commands, opts)


def repack_attrs(attrs):
    # repack attributes to a dict with attribute name being the key, from
    # [{'name': <attribute name>, 'value': <attribute value>},..]
    if attrs:
        return {v['name']: v['value'] for v in attrs}
    return {}


def dump_device_attributes(data):
    logging.debug('device data: %r', data)
    attrs = repack_attrs(data.get('attributes', None))
    print('attributes:')
    for k in sorted(attrs.keys()):
        print('  {:20}: {}'.format(k, attrs[k]))
    print('last update:', data['updated_ts'])


def device_show(opts):
    url = inventory_url(opts.service, '/devices/{}'.format(opts.device))
    rsp = requests.get(url, verify=opts.verify)
    logging.debug("%r", rsp.status_code)

    dump_device_attributes(rsp.json())


def device_group(opts):
    url = inventory_url(opts.service, '/devices/{}/group'.format(opts.device))
    if not opts.group_set and not opts.group_delete:
        do_simple_get(url, verify=opts.verify)
    elif opts.group_set:
        group = {
            'group': opts.group_set,
        }
        method = 'PUT'
    elif opts.group_delete:
        url = inventory_url(opts.service, '/devices/{}/group/{}'.format(opts.device,
                                                                        opts.group_delete))
        group = {
            'group': opts.group_delete,
        }
        method = 'DELETE'

    do_request(url, method=method, success=204,
               json=group, verify=opts.verify)


def device_attrs(opts):
    url = inventory_url(opts.service, '/devices/{}/attributes'.format(opts.device))
    if not opts.attrs_set:
        do_simple_get(url, verify=opts.verify)
    else:
        attrs = []
        for attr in opts.attrs_set:
            n, v = attr.split(':')
            attrs.append({'name': n, 'value': v})
        do_request(url, method='PATCH', json=attrs, verify=opts.verify)


def devices_list(opts):
    def devlist_printer(rsp):
        devslist = rsp.json()
        print ('devices:')
        for dev in devslist:
            attrs = repack_attrs(dev.get('attributes'))
            print('  {} (type: {}, updated: {})'.format(dev['id'],
                                                        attrs.get('device_type', '<undefined>'),
                                                        dev['updated_ts']))

    url = inventory_url(opts.service, '/devices')
    do_simple_get(url, printer=devlist_printer, verify=opts.verify)


def group_list(opts):
    url = inventory_url(opts.service, 'groups')
    do_simple_get(url, verify=opts.verify)


def group_show(opts):
    url = inventory_url(opts.service, 'groups/{}/devices'.format(opts.group))
    do_simple_get(url, verify=opts.verify)
