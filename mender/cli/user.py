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

from mender.cli.utils import api_from_opts, run_command, dump_token, \
    load_file, save_file
from mender.client import user_url


def add_args(sub):
    # deployments
    sub.set_defaults(usercommand='')

    pusub = sub.add_subparsers(help='Commands for user management')

    plogin = pusub.add_parser('login', help='Login')
    plogin.set_defaults(usercommand='login')
    plogin.add_argument('-u', '--user', help='User name', required=True)
    plogin.add_argument('-p', '--password', help='Password', required=True)

    ptoken = pusub.add_parser('token', help='Show token')
    ptoken.set_defaults(usercommand='token')

    plogininit = pusub.add_parser('initial-login', help='Initial login')
    plogininit.set_defaults(usercommand='initial-login')

    pinit = pusub.add_parser('initial', help='Initial user')
    pinit.set_defaults(usercommand='initial')
    pinit.add_argument('-u', '--user', help='User name', required=True)
    pinit.add_argument('-p', '--password', help='Password', required=True)


def do_main(opts):
    logging.debug('user opts: %r', opts)
    cmds = {
        'login': do_user_login,
        'token': do_user_token,
        'initial-login': do_user_login_initial,
        'initial': do_user_create_initial,
    }
    run_command(opts.usercommand, cmds, opts)


def do_user_login(opts):
    logging.debug('user login')

    url = user_url(opts.service, '/auth/login')
    with api_from_opts(opts) as api:
        # use basic auth with user provided password and login
        api.auth = (opts.user, opts.password)
        rsp = api.post(url)

        if rsp.status_code == 200:
            logging.info('request successful')
            logging.info('token: %s', rsp.text)
            save_file(opts.user_token, rsp.text)
        else:
            logging.warning('request failed: %s %s', rsp, rsp.text)


def do_user_login_initial(opts):
    logging.debug('initial user login')

    url = user_url(opts.service, '/auth/login')
    with api_from_opts(opts) as api:
        # use basic auth with user provided password and login
        api.auth = None
        rsp = api.post(url)

        if rsp.status_code == 200:
            logging.info('initial login successful')
            logging.info('token: %s', rsp.text)
            save_file(opts.user_token, rsp.text)
        else:
            logging.warning('request failed: %s %s', rsp, rsp.text)


def do_user_create_initial(opts):
    logging.debug('create initial user')

    url = user_url(opts.service, '/users/initial')
    with api_from_opts(opts) as api:
        # use basic auth with user provided password and login
        rsp = api.post(url,
                       json={
                           'email': opts.user,
                           'password': opts.password,
                       })
        if rsp.status_code == 201:
            logging.info('initial user created')
            logging.info(rsp.text)
        else:
            logging.warning('request failed: %s %s', rsp, rsp.text)


def do_user_token(opts):
    logging.info('show user token')
    try:
        tok = load_file(opts.user_token)
    except IOError as err:
        logging.error('failed to load token from %s: %s',
                      opts.user_token, err)
        return
    dump_token(tok)
