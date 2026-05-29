#!/bin/sh
set -eu

export PYTHONPATH=/app
exec python3 -m vds.server
