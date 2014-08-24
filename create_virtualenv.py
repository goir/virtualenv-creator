#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
import argparse
import hashlib
import subprocess
import sys
import os
import urllib2

WHEEL_PIP = 'https://pypi.python.org/packages/py2.py3/p/pip/pip-1.5.6-py2.py3-none-any.whl#md5=4d4fb4b69df6731c7aeaadd6300bc1f2'
WHEEL_SETUPTOOLS = 'https://pypi.python.org/packages/3.4/s/setuptools/setuptools-5.7-py2.py3-none-any.whl#md5=94eedce8d9b793d4affa4a85cd45edfa'


class Colors(object):
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    BLUE = '\033[34m'
    RESET = '\033[0m'


def call(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if args.debug:
        print("Executing command: {0}".format(cmd))
        print(p.stdout.read())
        print(p.stderr.read())
    p.wait()
    p.stdout.close()
    p.stderr.close()
    return p.returncode


def color(text, color):
    """ Color a string
    :param unicode text: the text the color to apply to
    :param unicode color: color to use
    :return: colored output
    :rtype: unicode
    """
    return "{color}{text}{reset}".format(color=getattr(Colors, color.upper()),
                                         text=text,
                                         reset=Colors.RESET)


def check_files_exists(req_files):
    """ Check if files exist. If not raise a RuntimeError

    :param list req_files: files to check for existence
    :return: None
    :exception: RuntimeError
    """
    for req_file in req_files:
        if not os.path.isfile(os.path.abspath(req_file)):
            raise RuntimeError(color('File {0} not found'.format(req_file), 'red'))
        else:
            print(color('Using requirements file {0}'.format(req_file), 'green'))


def create_wheels(req_file):
    """ Creates wheels in *wheel_dir* using *req_file*

    :param unicode req_file:
    :return: None
    """
    if call(['pip', 'install', '-U', 'wheel']) != 0:
        raise RuntimeError(color('could not install/update wheel', 'red'))
    print(color('Creating wheels from {0} into {1}'.format(req_file, args.wheels_dir), 'green'))

    if call(['pip', 'wheel', '--wheel-dir=%s' % args.wheels_dir, '-r', req_file]) != 0:
        raise RuntimeError(color('Creation of wheels from file {0} failed.'.format(req_file), 'red'))


def install_from_wheels(req_files, wheels_dir):
    """ Install requirements from wheels in *wheels_dir*. If this fails create_wheels() will be executed to (re-)create all wheels

    :param list req_files: List of requirement filenames
    :param unicode wheels_dir: dir where the wheels live
    :return: None
    """
    for req_file in req_files:
        print(color("Installing requirements from {0}".format(req_file), 'green'))
        install_cmd = ['pip', 'install', '-U', '--use-wheel', '--no-index', '--find-links=%s' % wheels_dir, '-r', req_file]
        if call(install_cmd) != 0:
            print(color('Not all requirements found in wheels dir. Re-creating all wheels', 'yellow'))
            create_wheels(req_file)
            # try again with the new wheels
            if call(install_cmd) != 0:
                raise RuntimeError(color("Installation of requirements from file {0} using wheels {1} failed".format(req_file, wheels_dir), 'red'))


def install_from_pypy(req_files):
    """ Install requirements from :param:req_files using live pypy.

    :param list req_files: List of requirement filenames
    :return: None
    """
    for req_file in req_files:
        print(color("Installing requirements from {0}".format(req_file), 'green'))
        install_cmd = ['pip', 'install', '-U', '-r', req_file]
        if call(install_cmd) != 0:
            raise RuntimeError(color("Installation of requirements from {0} using pypy failed".format(req_file), 'red'))


def download_wheel(url, target_dir):
    """ Download a wheel file from pypy. The url must have a #md5= in the url this is used to validate the download.
    This does nothing if the file already exists. And raises an Exception if the md5 checksum does not match.
    :param unicode url: download url
    :param unicode target_dir: Absolute path to directory to put the file in
    :return: None
    """
    url_split = url.split('#')
    filename = os.path.basename(url_split[0])
    md5_hash = url_split[1].split('md5=')[1]
    destination = os.path.join(target_dir, filename)
    # check if file already exists
    if os.path.isfile(destination):
        print(color('{0} already exists'.format(destination), 'yellow'))
    else:
        print(color('Downloading {0} to {1} from {2}'.format(filename, destination, url), 'green'))
        response = urllib2.urlopen(url)
        with open(destination, mode='wb') as fp:
            data = response.read()
            if md5_hash != hashlib.md5(data).hexdigest():
                os.unlink(destination)
                raise RuntimeError(color('md5 hash of file {0} does not match'.format(filename), 'red'))
            fp.write(data)


def create_virtualenv(root_path, target, wheels_dir):
    """ setup virtualenv in :param:target. Downloads Pip and Setuptools if they dont exist in *wheels_dir*.

    :param unicode root_path: Absolute path
    :param unicode target: Directory name for virtualenv in :param:root_path
    :param unicode wheels_dir: Absolute path where the wheels of pip and setuptools live or get downloaded to
    :return: None
    """
    # this is needed to get this filename even if executed by execfile()
    this_file = inspect.getframeinfo(inspect.currentframe()).filename
    venv_bin = os.path.join(os.path.abspath(os.path.dirname(this_file)), 'virtualenv.py')
    cmd = [sys.executable, venv_bin, os.path.join(root_path, target), '--no-site-packages', '--extra-search-dir', wheels_dir]

    if call(cmd) != 0:
        # most likeley pip and setuptools wheels could not be found
        # download them to wheels_dir.
        download_wheel(WHEEL_PIP, wheels_dir)
        download_wheel(WHEEL_SETUPTOOLS, wheels_dir)
        if call(cmd) != 0:
            raise RuntimeError(color('Could not setup virtualenv', 'red'))
    print(color("Created virtualenv in {0}".format(target), 'green'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help="activate debug output")
    parser.add_argument('--dev', '-d', action='store_true', help='install development requirements (requirements-dev.txt)')
    parser.add_argument('--target', '-t', type=str, default="env", help="where to put the new env (default: %(default)s)")
    parser.add_argument('--wheels', '-w', action='store_true', help="install from wheels. If a wheel does not exist it will be created")
    parser.add_argument('--wheels-dir', type=str, default=os.path.expanduser('~/.python_wheels'), help="install from wheels. If a wheel does not exist it will be created.")
    args = parser.parse_args()

    if not args.debug:
        def a(type, value, traceback):
            print(value)
        sys.excepthook = a

    # check if any environment is active
    if hasattr(sys, 'real_prefix'):
        raise RuntimeError(color('Please deactivate the current virtualenv using "deactivate"', 'red'))

    print(color("Using wheels dir {0}".format(args.wheels_dir), 'green'))
    # create the wheels dir if we use wheels
    try:
        os.mkdir(args.wheels_dir, 0o777)
    except OSError as e:
        # file already exists, ignore this
        pass

    requirement_files = ['requirements.txt']
    if args.dev:
        requirement_files.append('requirements-dev.txt')

    check_files_exists(requirement_files)

    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
    create_virtualenv(root_path, args.target, args.wheels_dir)

    # activate the new virtualenv
    activate_this = os.path.join(root_path, "%s/bin/activate_this.py" % args.target)
    exec(compile(open(activate_this).read(), activate_this, 'exec'), dict(__file__=activate_this))
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    if args.wheels:
        install_from_wheels(requirement_files, args.wheels_dir)
    else:
        install_from_pypy(requirement_files)

    print(color('Successfully installed all requirements from {0}'.format(', '.join(requirement_files)), 'green'))
