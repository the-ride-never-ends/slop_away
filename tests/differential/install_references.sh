#!/usr/bin/env bash
set -euo pipefail

destination=${1:?Set the virtual environment directory.}
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]]
temporary=$(mktemp -d)
trap 'rm -rf -- "$temporary"' EXIT
curl --fail --location --retry 3 --max-time 120 \
    --output "$temporary/vale.tar.gz" \
    https://github.com/vale-cli/vale/releases/download/v3.28.1/vale_3.28.1_Linux_64-bit.tar.gz
printf '%s  %s\n' \
    068954ad869ebec24b8dec6ebcd1cbb1fd5f5a83e966a35baedfae8b2cdc093a \
    "$temporary/vale.tar.gz" | sha256sum --check -
mkdir -p -- "$destination/bin" "$destination/share/nltk_data/corpora"
tar -xzf "$temporary/vale.tar.gz" -C "$destination/bin" vale
"$destination/bin/python" tests/differential/prepare_dictionary.py "$destination"
"$destination/bin/vale" --version
