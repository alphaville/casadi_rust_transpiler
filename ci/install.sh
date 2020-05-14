#!/bin/bash
set -euxo pipefail

main() {
    # Install necessary stuff
    rustup toolchain remove stable && rustup toolchain install stable
    sudo pip install --upgrade pip
    sudo pip install --upgrade virtualenv
    rustc --version
}

main
