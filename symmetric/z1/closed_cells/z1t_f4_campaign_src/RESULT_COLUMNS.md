# Result summary columns

Each terminal summary has 14 comma-separated fields:

1. `root_key`
2. `predicate`
3. `long_candidates`
4. `parity_admissible_records`
5. `long_seed_ok`
6. `seed_compatible_records`
7. `nodes`
8. `structural_covers`
9. `costas_covers`
10. `collision_prunes`
11. `z_prunes`
12. `sum_prunes`
13. `domain_prunes`
14. `status`

The complete campaign must satisfy:

```text
sum(long_candidates)           = 297838
sum(parity_admissible_records) = 15642886
```

`seed_compatible_records` is intentionally smaller when a long seed is rejected by the Costas or Z checks.
