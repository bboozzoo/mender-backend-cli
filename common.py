import logging

def run_command(command, cmds, opts):
    '''Locate and call `command` handler in a map `cmds`. The handler is called
    with `opts` as its first argument.

    Will throw a SystemExit(1) if command is not found.

    :param command: command as string
    :param cmds: map of commands, command name being the key, a function being the value
    :type cmds: map
    :param opts: options passed to command handler

    '''
    handler = cmds.get(command, None)
    if not handler:
        logging.error('command \'%s\' not supported', command)
        raise SystemExit(1)
    else:
        handler(opts)
