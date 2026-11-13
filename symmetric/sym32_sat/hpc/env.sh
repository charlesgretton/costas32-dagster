# hpc/env.sh -- environment for every job. Set COSTAS_DATA and the module versions for your own cluster.
# Edit PROJECT / COSTAS_DATA / DAGSTER_DIR once if yours differ.
if command -v module >/dev/null 2>&1; then
  module load openmpi/4.1.0
  module load python3/3.11.0 2>/dev/null || module load python3 2>/dev/null || true
fi
export PATH=$HOME/local/bin:$PATH
export CPATH=$HOME/local/include${CPATH:+:$CPATH}             # prepend: keep any CPATH you set
export LIBRARY_PATH=$HOME/local/lib${LIBRARY_PATH:+:$LIBRARY_PATH}   # prepend: keep any LIBRARY_PATH you set
export LD_LIBRARY_PATH=$HOME/local/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}   # append: keep openmpi's
export OMPI_MCA_btl=${OMPI_MCA_btl:-self,tcp}
export GLOG_logtostderr=1
# AFSAT-Integration Dagster (needs -e 3; prepare.sh checks)
export DAGSTER_DIR=${DAGSTER_DIR:-$HOME/dagster-afsat/dagster}
export DAGSTER_BIN=${DAGSTER_BIN:-$DAGSTER_DIR/dagster}
# Kissat built by prepare.sh into $HOME/local
export KISSAT=${KISSAT:-$HOME/local/bin/kissat}
# data and results on scratch (Lustre)
export COSTAS_DATA=${COSTAS_DATA:-$HOME/costas32_data}
# order 32 is production. Smaller values are ONLY for the smoke test.
export COSTAS_N=${COSTAS_N:-32}
# IMPORTANT. The XSA bundle uses "--map-by core --bind-to core", which is right when ONE
# mpirun owns the node. Here many shards run on one node at once; binding would stack every
# shard's Dagster onto cores 0..R-1. Each shard is instead confined by taskset to its own
# cores (run_shards.sh), and mpirun is told not to bind, so it stays inside that mask.
export MPIRUN_EXTRA=${MPIRUN_EXTRA:---bind-to none}

# Dagster solver flags. -m 3 = TiniSAT + clause strengthener, no local search.
# -p/-x/-y control TiniSAT restarting and have NO effect under -m 4 (MiniSat).
# NEVER -e 3: it stops at the first solution per message, so intermediate DAG
# nodes never enumerate and solutions are missed. pilot_driver.py refuses it.
export DAGSTER_FLAGS=${DAGSTER_FLAGS:--m 3 -e 0 -b 0 -g 1}
