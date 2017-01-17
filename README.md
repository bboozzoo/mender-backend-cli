## What is it?

A collection of cli tools for working with Mender backend.

Dependencies:
- Python 3
- requests
- requests-toolbelt
- pycrypto

## Tools

There's a separate tool for every service, each run as subcommand of
`mender-backend` script:

```
./mender-backend --help
usage: mender-backend [-h] [-d] [-s SERVICE] [-n]
                      {deployment,image,admission,inventory,device} ...

mender backend client

positional arguments:
  {deployment,image,admission,inventory,device}
                        Commands
    deployment          Deployments
    image               Images
    admission           Admission
    inventory           Inventory
    device              Device

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Enable debugging output (default: False)
  -s SERVICE, --service SERVICE
                        Service address (default:
                        https://docker.mender.io:8080/)
  -n, --no-verify       Skip certificate verification (default: False)
```

Each tool supports a number of commands, use `--help` for details.

## Installation

User-local installation:

```
python3 ./setup.py install --user
```

Make sure to have `~/.local/bin` in your `PATH`.
