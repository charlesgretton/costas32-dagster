CXX      ?= g++
CXXFLAGS ?= -O3 -march=native -std=c++17

BINS = solver/costas_fast solver/costas_dump rung/costas_rung rung/one_dot \
       propagation/ra_closure propagation/f3_complete propagation/tm_propagator \
       propagation/gen_benchmark12 propagation/verify_split propagation/f3prime_solver algebraic/gf32_expanded

all: $(BINS)

%: %.cpp
	$(CXX) $(CXXFLAGS) $< -o $@

# every self-test in the repository; all must pass before any result is trusted
selftest: check-files all
	@echo "== augmentation rung engine"
	./rung/costas_rung selftest
	@echo "== coordinate screening"
	python3 screening/costas_algebraic_screen.py selftest
	python3 screening/dual_exponential_screen.py selftest
	@echo "== SAT encoder vs brute force"
	python3 sat/gen_costas_dagster.py selftest
	@echo "== dyadic parity floor"
	python3 dyadic/dyadic_profile.py verify
	@echo "== m_2 >= 1 (signed-clique exhaustion)"
	python3 dyadic/m2_clique_search.py
	@echo "== F3 regression (guards both fixed bugs)"
	cd propagation && ./regression_f3.sh

clean:
	rm -f $(BINS)

.PHONY: all selftest clean

# reproducibility manifest: checksums of every tracked artefact plus toolchain
manifest:
	@echo "# costas32 manifest"                       >  MANIFEST.sha256
	@echo "# version: $$(cat VERSION)"                >> MANIFEST.sha256
	@echo "# generated: $$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> MANIFEST.sha256
	@echo "# compiler: $$($(CXX) --version | head -1)"   >> MANIFEST.sha256
	@echo "# python:   $$(python3 --version)"            >> MANIFEST.sha256
	@echo "# platform: $$(uname -srm)"                   >> MANIFEST.sha256
	@find . -type f ! -name MANIFEST.sha256 ! -path './.git/*' \
	      ! -name '*.o' ! -name '*.pyc' -print0 \
	  | sort -z | xargs -0 sha256sum                  >> MANIFEST.sha256
	@echo "wrote MANIFEST.sha256 ($$(grep -c '^[0-9a-f]' MANIFEST.sha256) files)"

# refuse to proceed if any expected artefact is missing
check-files:
	@for f in report/costas32_report.pdf catalogues/cat28.txt \
	          catalogues/cat29_census.txt rung/results/rung4_units.tar.gz \
	          rung/results/rung3_census164.txt propagation/f3_complete.cpp \
	          propagation/regression_f3.sh propagation/f3prime_results.json \
          proofs/INVENTORY.md proofs/STATUS.json VERSION README.md; do \
	    test -f $$f || { echo "MISSING: $$f"; exit 1; }; done
	@echo "all expected artefacts present"

.PHONY: manifest check-files

# proof-certification tracker
proof-status:
	@python3 tools/check_status.py
	@python3 -c "import json;d=json.load(open('proofs/STATUS.json'));s=d['summary'];\
print('report claims  :',s['report_claims']['total'],s['report_claims']['by_tier']);\
print('symmetric      :',s['symmetric_claims']['total'],s['symmetric_claims']['by_evidence']);\
print('registry total :',s['registry_objects_total']);\
print('withdrawn      :',len(d['withdrawn']));\
print('known gaps     :',len(d['known_gaps']))"


.PHONY: proof-status

# typecheck the Lean proofs (needs a lean 4.15.0 toolchain on PATH)
lean:
	cd proofs/lean && ./check.sh
.PHONY: lean

# --- registry and release gates ---------------------------------------------
registry-check:
	@python3 tools/check_status.py

release-check: check-files registry-check
	@python3 tools/check_compile.py
	@sha256sum -c MANIFEST.sha256 >/dev/null && echo "MANIFEST OK"
	@python3 tools/check_manifest_coverage.py
	@echo "RELEASE CHECK PASS"

check: registry-check
	@echo "CHECK PASS"

.PHONY: check registry-check release-check
