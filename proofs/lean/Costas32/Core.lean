/- Mathlib-free formalisation of the Tier A claims that do not need Finset. -/
namespace Costas32

/-- `win f k m = ∑_{i<m} f (k+i)`, a window of `m` terms starting at `k`. -/
def win (f : Nat → Int) (k : Nat) : Nat → Int
  | 0 => 0
  | m+1 => win f k m + f (k+m)

/-- `tsum g k = ∑_{i<k} g i`. -/
def tsum (g : Nat → Int) : Nat → Int
  | 0 => 0
  | k+1 => tsum g k + g k

/-- Shifting a window by one: the head leaves and a new tail arrives. -/
theorem win_shift (f : Nat → Int) (k m : Nat) :
    win f (k+1) m = win f k m + f (k+m) - f k := by
  induction m with
  | zero => simp [win]
  | succ m ih =>
      show win f (k+1) m + f (k+1+m) = win f k (m+1) + f (k+(m+1)) - f k
      rw [ih]
      show win f k m + f (k+m) - f k + f (k+1+m)
         = win f k m + f (k+m) + f (k+(m+1)) - f k
      have : k+1+m = k+(m+1) := by omega
      rw [this]; omega

/-- Windows split: `∑_{i<a+b} = ∑_{i<a} + ∑_{a≤i<a+b}`. -/
theorem win_split (f : Nat → Int) (a b : Nat) :
    win f 0 (a+b) = win f 0 a + win f a b := by
  induction b with
  | zero => simp [win]
  | succ b ih =>
      show win f 0 (a+b) + f (0+(a+b)) = win f 0 a + (win f a b + f (a+b))
      rw [ih]
      have : 0+(a+b) = a+b := by omega
      rw [this]; omega

/-- **Tier A5, the telescoping identity.**
    `∑_{i<k} (f(i+m) - f(i)) = ∑_{i<m} f(k+i) - ∑_{i<m} f(i)`. -/
theorem telescope (f : Nat → Int) (m : Nat) :
    ∀ k, tsum (fun i => f (i+m) - f i) k = win f k m - win f 0 m := by
  intro k
  induction k with
  | zero => simp [tsum, win]
  | succ k ih =>
      show tsum (fun i => f (i+m) - f i) k + (f (k+m) - f k) = win f (k+1) m - win f 0 m
      rw [ih, win_shift]; omega

/-- The telescoping sum at lag `m` of a sequence of length `n`. -/
def T (f : Nat → Int) (n m : Nat) : Int := win f (n-m) m - win f 0 m

/-- **`T m = T (n-m)`**, the symmetry used throughout the dyadic sections.
    Both equal `S - (∑ first m) - (∑ first (n-m))` where `S` is the total. -/
theorem T_symm (f : Nat → Int) (n m : Nat) (h : m ≤ n) :
    T f n m = T f n (n-m) := by
  have e1 : m + (n-m) = n := by omega
  have e2 : (n-m) + m = n := by omega
  have s1 := win_split f m (n-m)
  rw [e1] at s1
  have s2 := win_split f (n-m) m
  rw [e2] at s2
  have hnm : n - (n-m) = m := by omega
  simp only [T, hnm]
  omega

/-- **Tier A2 core, interval soundness.** If the exact quantity lies in two
    intervals that are disjoint, there is no completion. This is the logical
    heart of the `T_m` rule, separated from the implementation-specific work of
    showing each computed interval is an outer bound. -/
theorem tm_interval_sound {C : Type} {a b c d : Int} (exact : C → Int)
    (hl : ∀ σ, a ≤ exact σ ∧ exact σ ≤ b)
    (hr : ∀ σ, c ≤ exact σ ∧ exact σ ≤ d)
    (hd : b < c ∨ d < a) : C → False := by
  intro σ
  have h1 := hl σ
  have h2 := hr σ
  omega


/-! ### Tier A7: overdetermination does not imply inconsistency -/

/-- A complete signed graph whose edge labels form a *cut* labelling
    `λ i k = w i ⊕ w k` is consistent at every size: `v := w` satisfies every
    edge equation. So the number of equations exceeding the number of unknowns
    proves nothing, which is why the `m₂ ≥ 1` argument needs the midpoint
    structure and not merely a count. -/
theorem cut_labelling_consistent (w : Nat → Bool) :
    ∃ v : Nat → Bool, ∀ i k, (v i != v k) = (w i != w k) :=
  ⟨w, fun _ _ => rfl⟩

/-! ### Tier A1 fragments: the arithmetic core of the diagonal parity floor -/

/-- `2·C(e,2) + 2·C(16-e,2) = 2(e-8)² + 112` for every `e ≤ 16`, written
    without division. -/
def parityIdentityCheck : Bool :=
  (List.range 17).all (fun e =>
    let E : Int := e
    E * (E - 1) + (16 - E) * (15 - E) == 2 * ((E - 8) * (E - 8)) + 112)

theorem parity_identity : parityIdentityCheck = true := by decide

/-- The number of diagonal triples at order 32 is `∑_{m=1}^{15} (32-2m) = 240`. -/
def diagTripleCount : Nat :=
  ((List.range 16).map (fun m => 32 - 2 * (m + 1))).foldl (· + ·) 0

theorem diagTriples_240 : diagTripleCount = 240 := by decide

/-- ...which is exactly the number of same-parity index pairs, `2·C(16,2)`. -/
theorem sameParityPairs_240 : 2 * (16 * 15 / 2) = 240 := by decide

/-- The floor itself: the identity's minimum over `e ≤ 16` is 112, attained at
    `e = 8`. -/
def parityFloorCheck : Bool :=
  (List.range 17).all (fun e =>
    let E : Int := e
    112 ≤ 2 * ((E - 8) * (E - 8)) + 112)

theorem parity_floor_arith : parityFloorCheck = true := by decide

/-! ### Tier A3: the prime-power obstruction at order 32 -/

def isPrime (p : Nat) : Bool :=
  2 ≤ p && (List.range p).all (fun d => d < 2 || p % d != 0)

def isPrimePower (q : Nat) : Bool :=
  2 ≤ q &&
  ((List.range (q+1)).filter (fun p => 2 ≤ p && q % p == 0 && isPrime p)).length == 1

/-- A loss-free Welch or Golomb parameterisation at order `N` needs `N+1` or
    `N+2` to be a prime power. At `N = 32` neither is, and neither are the next
    two. -/
theorem no_prime_power_33 : isPrimePower 33 = false := by decide
theorem no_prime_power_34 : isPrimePower 34 = false := by decide
theorem no_prime_power_35 : isPrimePower 35 = false := by decide
theorem no_prime_power_36 : isPrimePower 36 = false := by decide

/-- By contrast 31 and 32 are, which is why order 30 has constructions. -/
theorem prime_power_31 : isPrimePower 31 = true := by decide
theorem prime_power_32 : isPrimePower 32 = true := by decide

end Costas32
