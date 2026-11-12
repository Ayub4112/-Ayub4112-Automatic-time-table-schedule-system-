#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/standalone-demo"
python3 -m http.server 8080
