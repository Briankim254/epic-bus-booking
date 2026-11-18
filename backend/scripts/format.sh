#!/usr/bin/env bash
set -e
set -x

ruff check app tests --fix
ruff format app tests
