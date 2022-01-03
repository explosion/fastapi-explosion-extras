#!/usr/bin/env bash

set -e

# Insist repository is clean
git diff-index --quiet HEAD

git checkout $1
git pull origin $1
git push origin $1

version=$(grep -m 1 "version = " pyproject.toml)
version=${version/version = }
version=${version/\'/}
version=${version/\'/}
version=${version/\"/}
version=${version/\"/}
git tag "v$version"
git push origin "v$version"