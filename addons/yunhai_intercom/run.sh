#!/bin/sh
set -eu

export PYTHONPATH=/app
exec python3 -m yunhai_intercom.server
