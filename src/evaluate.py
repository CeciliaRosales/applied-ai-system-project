"""
Evaluation / test harness for VibeMatch.

Runs the recommender over a fixed battery of cases and prints a machine- and
human-readable PASS/FAIL report plus a confidence summary. Unlike ``src/main.py``
(which just *shows* recommendations), this script asserts an *expectation* for
every case and reports whether the system met it. It exercises three reliability
behaviors:

  * guardrail   - malformed profiles are rejected, not crashed on
  * confidence  - coherent tastes produce a high-confidence top pick
  * abstain     - tastes that don't exist in the catalog are flagged low-confidence

Run with:  python -m src.evaluate
Exit code is 0 when every case passes, 1 otherwise (handy for CI).
"""

import logging
import sys
from typing import Callable, Dict, List, Optional, Tuple

from src.recommender import (
    load_songs,
    recommend_songs,
    validate_user_prefs,
    confidence_from_score,
    is_confident,
    CONFIDENCE_THRESHOLD,
)

logging.basicConfig(
    level=logging.WARNING,  # quiet during evaluation; only surface problems
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


# A case is (name, profile, expectation). `expectation` is one of:
#   "valid_confident" - passes validation AND top pick clears the threshold
#   "valid_abstain"   - passes validation BUT top pick is below the threshold
#   "invalid"         - fails validation (guardrail should reject it)
CASES: List[Tuple[str, Dict, str]] = [
    # --- Realistic profiles: should be accepted and confident ---
    ("High-Energy Pop", {
        "favorite_genre": "pop", "favorite_mood": "happy",
        "target_energy": 0.9, "likes_acoustic": False,
    }, "valid_confident"),
    ("Chill Lofi", {
        "favorite_genre": "lofi", "favorite_mood": "chill",
        "target_energy": 0.35, "likes_acoustic": True,
    }, "valid_confident"),
    ("Deep Intense Rock", {
        "favorite_genre": "rock", "favorite_mood": "intense",
        "target_energy": 0.9, "likes_acoustic": False,
    }, "valid_confident"),

    # --- Adversarial: valid input, but no real match -> should abstain ---
    ("Nonexistent Genre & Mood", {
        "favorite_genre": "k-pop", "favorite_mood": "sad",
        "target_energy": 0.5, "likes_acoustic": True,
    }, "valid_abstain"),

    # --- Malformed input: the guardrail should reject each of these ---
    ("Blank genre", {
        "favorite_genre": "", "favorite_mood": "chill",
        "target_energy": 0.5, "likes_acoustic": True,
    }, "invalid"),
    ("Energy out of range", {
        "favorite_genre": "pop", "favorite_mood": "happy",
        "target_energy": 4.0, "likes_acoustic": False,
    }, "invalid"),
    ("Missing likes_acoustic", {
        "favorite_genre": "pop", "favorite_mood": "happy",
        "target_energy": 0.5,
    }, "invalid"),
    ("likes_acoustic wrong type", {
        "favorite_genre": "pop", "favorite_mood": "happy",
        "target_energy": 0.5, "likes_acoustic": "yes",
    }, "invalid"),
]


def _evaluate_case(profile: Dict, expectation: str, songs: List[Dict]
                   ) -> Tuple[bool, Optional[float], str]:
    """Run one case. Returns (passed, top_confidence_or_None, detail)."""
    valid, errors = validate_user_prefs(profile)

    if expectation == "invalid":
        if valid:
            return False, None, "expected rejection but profile was accepted"
        return True, None, f"rejected ({len(errors)} error(s))"

    # From here on we expect a valid profile.
    if not valid:
        return False, None, f"expected valid but rejected: {errors}"

    ranked = recommend_songs(profile, songs, k=5)
    if len(ranked) != 5:
        return False, None, f"expected 5 recommendations, got {len(ranked)}"

    top_score = ranked[0][1]
    top_conf = confidence_from_score(top_score)
    confident = is_confident(top_score)

    if expectation == "valid_confident":
        passed = confident
        detail = f"top={ranked[0][0]['title']!r} conf={top_conf:.2f}"
        if not passed:
            detail += " (expected confident)"
        return passed, top_conf, detail

    if expectation == "valid_abstain":
        passed = not confident
        detail = f"abstained conf={top_conf:.2f}"
        if not passed:
            detail = f"expected abstain but was confident conf={top_conf:.2f}"
        return passed, top_conf, detail

    return False, top_conf, f"unknown expectation {expectation!r}"


def run(csv_path: str = "data/songs.csv") -> bool:
    """Run every case, print the report, and return True if all passed."""
    songs = load_songs(csv_path)

    print("=" * 72)
    print(f" VibeMatch Evaluation Harness  ({len(songs)} songs, "
          f"abstain threshold = {CONFIDENCE_THRESHOLD:.2f})")
    print("=" * 72)
    print(f"{'RESULT':<7} {'EXPECTATION':<16} {'CASE':<26} DETAIL")
    print("-" * 72)

    passed_count = 0
    confidences: List[float] = []
    for name, profile, expectation in CASES:
        passed, top_conf, detail = _evaluate_case(profile, expectation, songs)
        passed_count += int(passed)
        if top_conf is not None:
            confidences.append(top_conf)
        marker = "PASS " if passed else "FAIL "
        print(f"{marker:<7} {expectation:<16} {name:<26} {detail}")

    total = len(CASES)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    print("-" * 72)
    print(f"Summary: {passed_count}/{total} cases passed | "
          f"avg top-confidence (scored cases) = {avg_conf:.2f}")
    if passed_count == total:
        print("All reliability checks passed: guardrail, confidence, and abstain "
              "all behaved as expected.")
    else:
        print(f"{total - passed_count} case(s) failed — see FAIL rows above.")
    print("=" * 72)
    return passed_count == total


def main() -> None:
    ok = run()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
