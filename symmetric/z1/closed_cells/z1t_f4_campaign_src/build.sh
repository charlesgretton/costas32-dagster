#!/bin/sh
set -eu
cd "$(dirname "$0")"
${CXX:-g++} -O3 -march=native -std=c++17 -Wall -Wextra -Wshadow src/z1t_f4_search.cpp -o z1t_f4_search
${CXX:-g++} -O1 -g -std=c++17 -Wall -Wextra -Wshadow -fsanitize=address,undefined -fno-omit-frame-pointer src/z1t_f4_search.cpp -o z1t_f4_search_audit
sha256sum src/z1t_f4_search.cpp z1t_f4_search z1t_f4_search_audit > results/build_manifest.sha256
