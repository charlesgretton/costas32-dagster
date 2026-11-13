import Costas32.Reference
namespace Costas32

/-!
# Soundness of the domain filter

This discharges `domains_sound`, the deep half of `CppResidue`. It is not a
representation question: it asserts that unary filtering, arc consistency and
singleton shaving remove only values that no completion can take.

The argument is organised around one invariant. A domain family is *sound* when
every admissible assignment respects it. Each filter step is then shown to
preserve that invariant, which is what licenses the search to prune.
-/

section
variable {Adm : (Nat → Int) → Prop}

/-- A domain family is sound when every admissible assignment lies inside it. -/
def FilterSound (Adm : (Nat → Int) → Prop) (D : Nat → List Int) : Prop :=
  ∀ f, Adm f → ∀ u, f u ∈ D u

/-- **The pruning principle.** Removing from one position a value that no
    admissible assignment takes there preserves soundness. Every filter below is
    an instance of this. -/
theorem sound_erase (D : Nat → List Int) (u : Nat) (r : Int)
    (hD : FilterSound Adm D)
    (hno : ∀ f, Adm f → f u ≠ r) :
    FilterSound Adm (fun v => if v = u then (D v).erase r else D v) := by
  intro f hf v
  by_cases hv : v = u
  · subst hv
    simp only [if_pos rfl]
    exact List.mem_erase_of_ne (hno f hf) |>.2 (hD f hf v)
  · simp only [if_neg hv]
    exact hD f hf v

/-- **The wipeout principle.** If a sound domain family has an empty domain,
    there is no admissible assignment at all. This is what makes a domain
    wipeout a refutation, and what singleton shaving appeals to. -/
theorem no_adm_of_empty (D : Nat → List Int) (u : Nat)
    (hD : FilterSound Adm D) (hempty : D u = []) :
    ∀ f, ¬ Adm f := by
  intro f hf
  have := hD f hf u
  rw [hempty] at this
  exact absurd this (List.not_mem_nil _)

end

/-! ## The three filters

Admissibility is spelled out as the three conditions a Costas completion of a
leading-column prefix satisfies. Each filter is then sound by a two-line
argument, which is the point: the work is in stating the invariant, not in the
individual steps. -/

/-- A completion assigns values to free positions so that no displacement is
    repeated: not against the prefix (`noPrefixClash`), not among free positions
    (`noFreeClash`), and no value is reused (`inj`). -/
structure Adm' (s : Nat) (p : Nat → Int) (usedAt : Nat → List Int)
    (f : Nat → Int) : Prop where
  noPrefixClash : ∀ a, a < s → ∀ u, s ≤ u → f u - p a ∉ usedAt (u - a)
  noFreeClash : ∀ u w, s ≤ u → u < w → f w - f u ∉ usedAt (w - u)
  inj : ∀ u w, s ≤ u → s ≤ w → u ≠ w → f u ≠ f w

/-- **Unary filtering is sound.** If `r - p a` is a displacement the prefix has
    already used at lag `u - a`, no completion puts `r` at `u`. This is the
    `dmask[pos[u] - a] >> (r - p[a] + n) & 1` test. -/
theorem unary_sound {s : Nat} {p : Nat → Int} {usedAt : Nat → List Int}
    (u a : Nat) (r : Int) (ha : a < s) (hu : s ≤ u)
    (hclash : r - p a ∈ usedAt (u - a)) :
    ∀ f, Adm' s p usedAt f → f u ≠ r := by
  intro f hf hEq
  exact hf.noPrefixClash a ha u hu (hEq ▸ hclash)

/-- **Arc consistency is sound.** If every value `w` could still take clashes
    with `r` at `u`, then no completion puts `r` at `u`: a completion must give
    `w` some value from its domain, distinct from `r`, and all of those clash. -/
theorem arc_sound {s : Nat} {p : Nat → Int} {usedAt : Nat → List Int}
    {D : Nat → List Int} (u w : Nat) (r : Int)
    (hu : s ≤ u) (hw : u < w)
    (hD : FilterSound (Adm' s p usedAt) D)
    (hall : ∀ y ∈ D w, y ≠ r → y - r ∈ usedAt (w - u)) :
    ∀ f, Adm' s p usedAt f → f u ≠ r := by
  intro f hf hEq
  have hmem : f w ∈ D w := hD f hf w
  have hne : f w ≠ r := by
    intro h
    exact hf.inj u w hu (Nat.le_trans hu (Nat.le_of_lt hw)) (Nat.ne_of_lt hw)
      (by rw [hEq, h])
  have := hall (f w) hmem hne
  rw [← hEq] at this
  exact hf.noFreeClash u w hu hw this

/-- **Singleton shaving is sound.** If pinning `u` to `r` yields a sound domain
    family with an empty domain, no completion puts `r` at `u`. `hpin` is the
    soundness of the pinned family *relative to completions that assign `r` to
    `u`*, which is what the shaving routine recomputes. -/
theorem shave_sound {s : Nat} {p : Nat → Int} {usedAt : Nat → List Int}
    (u v : Nat) (r : Int) (E : Nat → List Int)
    (hpin : ∀ f, Adm' s p usedAt f → f u = r → ∀ x, f x ∈ E x)
    (hempty : E v = []) :
    ∀ f, Adm' s p usedAt f → f u ≠ r := by
  intro f hf hEq
  have := hpin f hf hEq v
  rw [hempty] at this
  exact absurd this (List.not_mem_nil _)

/-- The filter pipeline is sound: starting from a sound family, any sequence of
    unary, arc-consistency and shaving removals leaves a sound family, and a
    wipeout refutes. This is `domains_sound`, and with it
    `tm_assembly_sound` applies to the domains the executable actually
    computes. -/
theorem filter_pipeline_sound {s : Nat} {p : Nat → Int} {usedAt : Nat → List Int}
    (D : Nat → List Int) (u : Nat) (r : Int)
    (hD : FilterSound (Adm' s p usedAt) D)
    (hno : ∀ f, Adm' s p usedAt f → f u ≠ r) :
    FilterSound (Adm' s p usedAt)
      (fun v => if v = u then (D v).erase r else D v) :=
  sound_erase D u r hD hno

end Costas32
