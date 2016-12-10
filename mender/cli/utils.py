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
import requests

from mender.client import ApiClient


def run_command(command, cmds, opts):
    '''Locate and call `command` handler in a map `cmds`. The handler is called
    with `opts` as its first argument.

    Will raise CommandNotSupport(command) if command is not found.

    :param command: command as string
    :param cmds: map of commands, command name being the key, a function being the value
    :type cmds: map
    :param opts: options passed to command handler

    '''
    handler = cmds.get(command, None)
    if not handler:
        raise CommandNotSupportedError(command)
    else:
        handler(opts)


class CommandNotSupportedError(Exception):
    """Indicates that `command` is not supported"""
    def __init__(self, command):
        super().__init__(command)
        self.command = command
    def __str__(self):
        return 'command {} is not supported'.format(self.command)


def api_from_opts(opts):
    api = ApiClient()
    if opts.no_verify:
        api.verify = False
    if opts.cacert:
        api.verify = opts.cacert
    return api
