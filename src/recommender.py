import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file into a list of dicts, converting numeric columns to int/float."""
    int_fields = ("id", "tempo_bpm")
    float_fields = ("energy", "valence", "danceability", "acousticness")

    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song = dict(row)
            for field in int_fields:
                song[field] = int(song[field])
            for field in float_fields:
                song[field] = float(song[field])
            songs.append(song)
    return songs

# --- Algorithm Recipe weights (see README "How The System Works") ---
GENRE_WEIGHT = 2.0
MOOD_WEIGHT = 1.0
ENERGY_WEIGHT = 1.0      # multiplied by an energy "closeness" value in 0..1
ACOUSTIC_WEIGHT = 0.5
ACOUSTIC_THRESHOLD = 0.5  # acousticness above this counts as an "acoustic" song


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against user preferences, returning (score, reasons) where reasons explains each point."""
    score = 0.0
    reasons: List[str] = []

    # 1. Genre match (exact string) -> strongest signal
    if song["genre"] == user_prefs.get("favorite_genre"):
        score += GENRE_WEIGHT
        reasons.append(f"genre match ({song['genre']}) (+{GENRE_WEIGHT})")

    # 2. Mood match (exact string)
    if song["mood"] == user_prefs.get("favorite_mood"):
        score += MOOD_WEIGHT
        reasons.append(f"mood match ({song['mood']}) (+{MOOD_WEIGHT})")

    # 3. Energy closeness -> reward how NEAR the energy is to the target,
    #    not just high or low. 1.0 = identical, approaches 0.0 as it diverges.
    target_energy = user_prefs.get("target_energy")
    if target_energy is not None:
        closeness = 1 - abs(song["energy"] - target_energy)
        energy_points = closeness * ENERGY_WEIGHT
        score += energy_points
        reasons.append(
            f"energy closeness (song {song['energy']:.2f} vs target "
            f"{target_energy:.2f}) (+{energy_points:.2f})"
        )

    # 4. Acoustic preference -> small nudge when the song's acoustic style
    #    agrees with the user's yes/no preference (matches in both directions).
    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None:
        is_acoustic = song["acousticness"] > ACOUSTIC_THRESHOLD
        if is_acoustic == likes_acoustic:
            style = "acoustic" if likes_acoustic else "non-acoustic"
            score += ACOUSTIC_WEIGHT
            reasons.append(f"{style} preference match (+{ACOUSTIC_WEIGHT})")

    if not reasons:
        reasons.append("no matching preferences")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song and return the top k as (song, score, explanation) tuples, ranked highest first."""
    # Score every song. Each entry is (song, score, explanation).
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "; ".join(reasons)
        scored.append((song, score, explanation))

    # Rank: sorted() returns a NEW list; key picks the score (index 1);
    # reverse=True puts the highest score first.
    ranked = sorted(scored, key=lambda entry: entry[1], reverse=True)

    return ranked[:k]
