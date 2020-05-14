#!/bin/bash
set -euxo pipefail

regular_test() {
    export PYTHONPATH=.
    virtualenv -p python$PYTHON_VERSION venv
    source venv/bin/activate
    python setup.py install
    python -W ignore tests/test.py -v
}


main() {
   echo "Running tests"
        regular_test
}

main
