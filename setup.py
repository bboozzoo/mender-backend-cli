from setuptools import setup, find_packages

NAME = 'mender-backend-cli'
VERSION = '0.1'

install_reqires = ['requests', 'pycrypto']

setup(name=NAME,
      version=VERSION,
      packages=find_packages(exclude=['tests', 'tests.*']),
      description='CLI for interacting with mender.io backend services',
      author='Maciej Borzecki',
      author_email='maciek.borzecki@gmail.com',
      license='Apache-2.0',
      install_requires=install_reqires,
      scripts=['mender-backend'])
