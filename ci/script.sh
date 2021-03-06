#!/bin/bash
set -euxo pipefail

regular_test() {
    export PYTHONPATH=.
    virtualenv -p python$PYTHON_VERSION venv
    ls
    virtualenv --version
    set +u
    source venv/bin/activate
    set -u
    python setup.py install
    python -W ignore tests/unit_tests.py -v
    python -W ignore tests/integration_tests.py -v
}


main() {
    echo "Running tests"
    regular_test
}

main

