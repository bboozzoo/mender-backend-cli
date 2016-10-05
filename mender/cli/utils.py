import requests

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
