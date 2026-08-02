from src.recommender import (
    Song,
    UserProfile,
    Recommender,
    validate_user_prefs,
    confidence_from_score,
    is_confident,
    recommend_songs,
    load_songs,
    MAX_SCORE,
    CONFIDENCE_THRESHOLD,
)

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# --- Reliability layer: input-validation guardrail ---

def _good_prefs() -> dict:
    return {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    }


def test_validate_accepts_good_prefs():
    valid, errors = validate_user_prefs(_good_prefs())
    assert valid is True
    assert errors == []


def test_validate_rejects_blank_genre():
    prefs = _good_prefs()
    prefs["favorite_genre"] = "   "
    valid, errors = validate_user_prefs(prefs)
    assert valid is False
    assert any("favorite_genre" in e for e in errors)


def test_validate_rejects_energy_out_of_range():
    prefs = _good_prefs()
    prefs["target_energy"] = 4.0
    valid, errors = validate_user_prefs(prefs)
    assert valid is False
    assert any("target_energy" in e for e in errors)


def test_validate_rejects_bool_energy():
    # bool is a subclass of int, so True must NOT count as a valid energy value.
    prefs = _good_prefs()
    prefs["target_energy"] = True
    valid, errors = validate_user_prefs(prefs)
    assert valid is False


def test_validate_rejects_missing_key():
    prefs = _good_prefs()
    del prefs["likes_acoustic"]
    valid, errors = validate_user_prefs(prefs)
    assert valid is False


# --- Reliability layer: confidence scoring ---

def test_confidence_is_bounded_0_to_1():
    assert confidence_from_score(-5) == 0.0
    assert confidence_from_score(0) == 0.0
    assert confidence_from_score(MAX_SCORE) == 1.0
    assert confidence_from_score(MAX_SCORE * 2) == 1.0


def test_confidence_is_monotonic():
    assert confidence_from_score(1.0) < confidence_from_score(3.0)


def test_is_confident_respects_threshold():
    low = (CONFIDENCE_THRESHOLD * MAX_SCORE) - 0.5
    high = (CONFIDENCE_THRESHOLD * MAX_SCORE) + 0.5
    assert is_confident(low) is False
    assert is_confident(high) is True


# --- Reliability layer: abstain behavior on a nonexistent taste ---

def test_nonexistent_taste_yields_low_confidence(tmp_path):
    """A genre+mood absent from the catalog can never fire the categorical
    rules, so the top pick should fall below the abstain threshold."""
    songs = load_songs("data/songs.csv")
    prefs = {
        "favorite_genre": "k-pop",   # not in the catalog
        "favorite_mood": "sad",      # not in the catalog
        "target_energy": 0.5,
        "likes_acoustic": True,
    }
    ranked = recommend_songs(prefs, songs, k=5)
    assert len(ranked) == 5
    top_score = ranked[0][1]
    assert is_confident(top_score) is False
