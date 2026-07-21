"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


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
    """Print the top k recommendations for one named taste profile."""
    profile_line = (
        f"genre={user_prefs['favorite_genre']} | "
        f"mood={user_prefs['favorite_mood']} | "
        f"target_energy={user_prefs['target_energy']} | "
        f"likes_acoustic={user_prefs['likes_acoustic']}"
    )

    print()
    print("=" * 60)
    print(f" {name} - Top {k}")
    print(f" {profile_line}")
    print("=" * 60)

    for rank, (song, score, explanation) in enumerate(
        recommend_songs(user_prefs, songs, k=k), start=1
    ):
        print()
        print(f"{rank}. {song['title']} - {song['artist']}")
        print(f"   Genre/Mood: {song['genre']} / {song['mood']}")
        print(f"   Score: {score:.2f} / 4.5")
        print("   Reasons:")
        # explanation is a "; "-joined string from score_song's reasons list
        for reason in explanation.split("; "):
            print(f"     - {reason}")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for name, user_prefs in PROFILES:
        show_recommendations(name, user_prefs, songs, k=5)


if __name__ == "__main__":
    main()
