#!/bin/bash

set -euo pipefail

if [ -z "${STRATEGY:-}" ]; then
    # There's nothing to do
    exit 0
fi

if [ "$STRATEGY" == "min" ]; then
    # Install the minversion of tox as specified in tox.ini
    pip install "tox==$(./tools/extremal_dependency_versions.py get_tox_minversion)"
fi

if [ "$STRATEGY" == "dev" ]; then
    # Install Rust, which we'll need to build Qiskit Terra
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi

# Update pyproject.toml with the pinned dependencies
./tools/extremal_dependency_versions.py pin_dependencies "$STRATEGY" --inplace
