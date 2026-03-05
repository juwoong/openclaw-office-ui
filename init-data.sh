#!/bin/bash
set -e

mkdir -p data
mkdir -p data/memory

if [ ! -f data/state.json ]; then
  cp state.sample.json data/state.json
fi

if [ ! -f data/join-keys.json ]; then
  cp join-keys.sample.json data/join-keys.json
fi

if [ ! -f data/agents-state.json ]; then
  echo '[]' > data/agents-state.json
fi

echo "data/ initialized."
