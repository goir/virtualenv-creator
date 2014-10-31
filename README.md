virtualenv-creator
==================

If you requirements contain a lot of modules or modules which take a long time to build this little script might help you.
It can create *wheel* files for you requirements on the first setup and reuses them in future virtualenv setups.

Currently it requires files to be named *requirements.txt* and *requirements-dev.txt*

More and better doc and tests will come soon!

To create a development environment use
  python bin/create_virtualenv.py -d


usage: create_virtualenv.py [-h] [--debug] [--dev] [--target TARGET]
                            [--wheels] [--wheels-dir WHEELS_DIR]

optional arguments:
  -h, --help            show this help message and exit
  --debug               activate debug output
  --dev, -d             install development requirements (requirements-
                        dev.txt)
  --target TARGET, -t TARGET
                        where to put the new env (default: env)
  --wheels, -w          install from wheels. If a wheel does not exist it will
                        be created
  --wheels-dir WHEELS_DIR
                        install from wheels. If a wheel does not exist it will
                        be created.
