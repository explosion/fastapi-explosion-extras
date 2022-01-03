#!/bin/sh -e
set -x

autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place fastapi_extras tests --exclude=__init__.py
black fastapi_extras tests docs/src
isort fastapi_extras tests docs/src