#!/usr/bin/env bash

set -e
set -x

# mypy fastapi_extras --disallow-untyped-defs
black fastapi_extras tests --check
isort fastapi_extras tests --check-only