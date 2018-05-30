from glob import glob
from os.path import basename, splitext
from setuptools import setup, find_packages

VERSION = '0.0.2'

setup(
    name='ansible_inventory_manage',
    author='Jean-Philippe Evrard',
    author_email='jean-philippe@evrard.me',
    description='Ansible Inventory CRUD library',
    install_requires=['future'],
    license='Apache License 2.0',
    long_description=open('README.rst').read(),
    packages=find_packages('src/'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    tests_require=['pytest', 'tox'],
    url='https://github.com/evrardjp/ansible-inventory-manage',
    version=VERSION,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
