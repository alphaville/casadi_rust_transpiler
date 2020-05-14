#!/bin/bash
set -euxo pipefail

main() {
    # Install necessary stuff
    sudo pip install --upgrade pip
    sudo pip install virtualenv --upgrade --ignore-installed six
}

main
