"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Example "taste profile". Keys match the fields described in the README
    # and used by score_song(): favorite_genre, favorite_mood, target_energy,
    # likes_acoustic.
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    }

    k = 5
    recommendations = recommend_songs(user_prefs, songs, k=k)

    # --- Formatted output ---------------------------------------------------
    profile_line = (
        f"genre={user_prefs['favorite_genre']} | "
        f"mood={user_prefs['favorite_mood']} | "
        f"target_energy={user_prefs['target_energy']} | "
        f"likes_acoustic={user_prefs['likes_acoustic']}"
    )

    print()
    print("=" * 60)
    print(f" Top {k} recommendations for your taste profile")
    print(f" {profile_line}")
    print("=" * 60)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print()
        print(f"{rank}. {song['title']} - {song['artist']}")
        print(f"   Genre/Mood: {song['genre']} / {song['mood']}")
        print(f"   Score: {score:.2f} / 4.5")
        print("   Reasons:")
        # explanation is a "; "-joined string from score_song's reasons list
        for reason in explanation.split("; "):
            print(f"     - {reason}")


if __name__ == "__main__":
    main()
