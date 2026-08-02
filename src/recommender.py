import csv
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict

# Module logger. The application entry point (src/main.py, src/evaluate.py)
# configures the root logger; here we just obtain a named logger so every
# reliability event (rejected input, abstain decisions) is traceable.
logger = logging.getLogger("vibematch")

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

    @staticmethod
    def _prefs(user: UserProfile) -> Dict:
        """Turn a UserProfile into the dict that score_song() expects."""
        return {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Score every song for this user and return the top k Song objects, best first."""
        prefs = self._prefs(user)
        scored = [(song, score_song(prefs, asdict(song))[0]) for song in self.songs]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why this song fits the user."""
        score, reasons = score_song(self._prefs(user), asdict(song))
        return f"{song.title} scored {score:.2f}/4.5 - " + "; ".join(reasons)

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

def validate_user_prefs(user_prefs: Dict) -> Tuple[bool, List[str]]:
    """Guardrail: check a user-preferences dict before it reaches the scorer.

    Returns ``(is_valid, errors)``. When invalid, ``errors`` lists every problem
    found (so the caller can show all of them at once) and the failure is logged.
    Keeping bad input out of ``score_song`` is what stops the pipeline from
    crashing on missing keys or nonsensical values.
    """
    errors: List[str] = []

    genre = user_prefs.get("favorite_genre")
    mood = user_prefs.get("favorite_mood")
    target_energy = user_prefs.get("target_energy")
    likes_acoustic = user_prefs.get("likes_acoustic")

    if not isinstance(genre, str) or not genre.strip():
        errors.append("favorite_genre must be a non-empty string.")

    if not isinstance(mood, str) or not mood.strip():
        errors.append("favorite_mood must be a non-empty string.")

    # bool is a subclass of int, so reject it explicitly for a numeric field.
    if (isinstance(target_energy, bool)
            or not isinstance(target_energy, (int, float))
            or not 0 <= target_energy <= 1):
        errors.append("target_energy must be a number between 0 and 1.")

    if not isinstance(likes_acoustic, bool):
        errors.append("likes_acoustic must be either True or False.")

    is_valid = not errors
    if not is_valid:
        logger.warning("Rejected invalid user preferences: %s", errors)
    return is_valid, errors

# --- Algorithm Recipe weights (see README "How The System Works") ---
# (A sensitivity experiment temporarily used GENRE_WEIGHT = 1.0 and
# ENERGY_WEIGHT = 2.0; reverted to the finalized recipe below.)
GENRE_WEIGHT = 2.0
MOOD_WEIGHT = 1.0
ENERGY_WEIGHT = 1.0      # multiplied by an energy "closeness" value in 0..1
ACOUSTIC_WEIGHT = 0.5
ACOUSTIC_THRESHOLD = 0.5  # acousticness above this counts as an "acoustic" song

# --- Reliability layer: confidence + abstain ---
# The most points any single song can earn (genre + mood + energy + acoustic).
MAX_SCORE = GENRE_WEIGHT + MOOD_WEIGHT + ENERGY_WEIGHT + ACOUSTIC_WEIGHT  # 4.5

# If the TOP recommendation's confidence is below this, the system abstains
# ("no strong matches found") instead of confidently returning weak guesses.
# Calibration: realistic profiles top out ~0.98; a profile whose genre and mood
# don't exist in the catalog tops out ~0.32 (energy + acoustic only). 0.5 draws
# the line between "a real category matched" and "only weak signals fired."
CONFIDENCE_THRESHOLD = 0.5


def confidence_from_score(score: float) -> float:
    """Normalize a raw 0..MAX_SCORE song score into a 0..1 confidence value."""
    if MAX_SCORE <= 0:
        return 0.0
    return round(min(max(score / MAX_SCORE, 0.0), 1.0), 2)


def is_confident(score: float) -> bool:
    """True when a score clears the abstain threshold (a strong-enough match)."""
    return confidence_from_score(score) >= CONFIDENCE_THRESHOLD


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
