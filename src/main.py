"""
Command line runner for the VibeMatch Music Recommender.

Running ``python -m src.main`` loads the catalog and prints the top-5
recommendations for several taste profiles. Every profile now passes through
the reliability layer first:

  1. validate_user_prefs  -> guardrail: bad input is rejected, not crashed on
  2. recommend_songs      -> score + rank the catalog
  3. confidence_from_score-> each pick gets a 0..1 confidence
  4. abstain check        -> if the top pick is weak, say so instead of bluffing

All of these events are also written to the log.
"""

import logging

from src.recommender import (
    load_songs,
    recommend_songs,
    validate_user_prefs,
    confidence_from_score,
    is_confident,
    CONFIDENCE_THRESHOLD,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("vibematch.main")


# Taste profiles to try. Keys match the fields used by score_song():
# favorite_genre, favorite_mood, target_energy, likes_acoustic.
#
# The first three are realistic listeners; the last three are deliberately
# "adversarial" edge cases designed to see whether the scoring logic can be
# tricked or produces surprising results.
PROFILES = [
    ("High-Energy Pop", {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.9,
        "likes_acoustic": False,
    }),
    ("Chill Lofi", {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.35,
        "likes_acoustic": True,
    }),
    ("Deep Intense Rock", {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.9,
        "likes_acoustic": False,
    }),
    # --- Adversarial / edge-case profiles ---
    ("Adversarial: Conflicting Energy vs Mood", {
        # melancholic classical music is low-energy, but the user asks for 0.95
        "favorite_genre": "classical",
        "favorite_mood": "melancholic",
        "target_energy": 0.95,
        "likes_acoustic": False,
    }),
    ("Adversarial: Nonexistent Genre & Mood", {
        # neither "k-pop" nor "sad" exist in the catalog, so the categorical
        # rules can never fire
        "favorite_genre": "k-pop",
        "favorite_mood": "sad",
        "target_energy": 0.5,
        "likes_acoustic": True,
    }),
    ("Adversarial: Impossible Combo (peaceful acoustic metal)", {
        # genre pulls toward loud aggressive metal; every other field wants the
        # opposite
        "favorite_genre": "metal",
        "favorite_mood": "peaceful",
        "target_energy": 0.2,
        "likes_acoustic": True,
    }),
]


def show_recommendations(name: str, user_prefs: dict, songs: list, k: int = 5) -> None:
    """Print the top k recommendations for one named taste profile.

    The profile is validated first (guardrail); each pick is shown with a
    confidence value; and if the top pick's confidence is below the abstain
    threshold the system says so instead of presenting weak guesses as answers.
    """
    print()
    print("=" * 60)
    print(f" {name} - Top {k}")

    # --- Guardrail: reject bad input instead of crashing the scorer. ---
    valid, errors = validate_user_prefs(user_prefs)
    if not valid:
        print("=" * 60)
        print(" [REJECTED] Invalid taste profile:")
        for err in errors:
            print(f"   - {err}")
        return

    profile_line = (
        f"genre={user_prefs['favorite_genre']} | "
        f"mood={user_prefs['favorite_mood']} | "
        f"target_energy={user_prefs['target_energy']} | "
        f"likes_acoustic={user_prefs['likes_acoustic']}"
    )
    print(f" {profile_line}")
    print("=" * 60)

    ranked = recommend_songs(user_prefs, songs, k=k)
    logger.info("Profile %r -> top score %.2f", name, ranked[0][1] if ranked else 0.0)

    # --- Abstain check: is the single best match actually strong? ---
    top_score = ranked[0][1] if ranked else 0.0
    if not is_confident(top_score):
        print()
        print(f" [!] No strong matches found (top confidence "
              f"{confidence_from_score(top_score):.2f} < {CONFIDENCE_THRESHOLD:.2f}).")
        print("     Showing best-effort guesses only; treat these as low-confidence.")
        logger.warning("Abstain for profile %r: top confidence %.2f below threshold %.2f",
                       name, confidence_from_score(top_score), CONFIDENCE_THRESHOLD)

    for rank, (song, score, explanation) in enumerate(ranked, start=1):
        confidence = confidence_from_score(score)
        print()
        print(f"{rank}. {song['title']} - {song['artist']}")
        print(f"   Genre/Mood: {song['genre']} / {song['mood']}")
        print(f"   Score: {score:.2f} / 4.5   Confidence: {confidence:.2f}")
        print("   Reasons:")
        # explanation is a "; "-joined string from score_song's reasons list
        for reason in explanation.split("; "):
            print(f"     - {reason}")


def main() -> None:
    songs = load_songs("data/songs.csv")
    logger.info("Loaded %d songs from data/songs.csv", len(songs))
    print(f"Loaded songs: {len(songs)}")

    for name, user_prefs in PROFILES:
        show_recommendations(name, user_prefs, songs, k=5)


if __name__ == "__main__":
    main()
