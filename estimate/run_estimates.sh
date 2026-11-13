#!/bin/sh
# Reproduces the cost study: exact counts (orders 10-14), estimator validation (12-16),
# order-32 estimates by three Knuth seeds and two stratified depths, orders 29-31, and the order-32 node rate.
set -e
gcc -O3 -march=native -o costas_tree costas_tree.c -lm
for n in 10 11 12 13 14; do ./costas_tree exact $n; done
for n in 12 13 14 15 16; do ./costas_tree knuth $n 1000000 1; ./costas_tree strat $n 3 200 1; ./costas_tree strat $n 4 50 1; done
for n in 29 30 31; do ./costas_tree knuth $n 1000000 11; done
for s in 21 22 23; do ./costas_tree knuth 32 2000000 $s; done
./costas_tree strat 32 3 100 31
./costas_tree strat 32 4 10 32
./costas_tree rate 32 60
