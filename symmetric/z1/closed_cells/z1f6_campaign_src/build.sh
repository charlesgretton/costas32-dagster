#!/bin/sh
set -eu
cd "$(dirname "$0")"
${CXX:-g++} -O3 -march=native -std=c++17 -Wall -Wextra -Wshadow src/z1f6_search.cpp -o z1f6_search
sha256sum src/z1f6_search.cpp z1f6_search > results/build_manifest.sha256
