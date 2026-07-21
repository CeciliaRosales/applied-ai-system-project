# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Explain your design in plain language.
My music recommender is a content-based system. It matches songs to a user by comparing the attributes of each song against the user's stated taste, then ranks the best matches. It works in two steps: score every song, then rank the scored list. 

Some prompts to answer:

- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo
  Each song carries three kinds of information:
    - Identity: id, title, artist — used to label results, not to score them
    - Categories (labels): genre (pop, lofi, rock, jazz...) and mood (happy, chill, intense...)
    - Numeric audio features (0-1): energy, valence, danceability, and acousticness, plus tempo_bpm (60-152). These describe the feel of the track

    My scoring focuses on genre, mood, energy, and acousticness, because those are the attributes my user profile actually expresses a preference about

- What information does your `UserProfile` store
  - The user profile stores four taste preferences:
    - favorite_genre — the category of music they want most
    - favorite_mood — the vibe they're after
    - target_energy — how energetic they like their music, as a number from 0 to 1
    - likes_acoustic — a yes/no for whether they prefer acoustic songs

- How does your `Recommender` compute a score for each song
  - The recommender computes a score for each song by using an additive scoring rule: every song starts at 0, and it earns points for each way it matches the user. Higher total = better match.

  **Algorithm Recipe (finalized weights):**
    - +2.0 if the song's genre matches the user's favorite genre
    - +1.0 if the mood matches
    - +0 to +1.0 for energy, based on how close the song's energy is to the user's target — scored as `(1 - |song_energy - target_energy|) * 1.0`, so a perfect match earns the full point and the score drops as the gap widens (it rewards nearness, not just high or low values)
    - +0.5 if the song's acoustic style agrees with the user's likes_acoustic preference (i.e. `acousticness > 0.5` matches the boolean)

    Maximum possible score = **4.5**.

    I chose these weights so the features stay in a clear priority order: **genre (2.0) > mood (1.0) = energy-max (1.0) > acoustic (0.5)**. I weighted genre highest because it is a more reliable, specific signal, while moods overlap across very different songs (e.g. "intense" covers both rock and pop). I deliberately capped energy at 1.0 rather than 2.0 so that a numeric feature can break ties and outweigh a mood match, but can never override the primary genre intent. Acoustic is a small +0.5 nudge that honors the `likes_acoustic` field without letting a single yes/no swing the results. As it scores, the system also collects a list of reasons (e.g. "matches your favorite genre"), which is how it can explain each recommendation.

- How do you choose which songs to recommend
  - I choose which songs to recommend after scoring every song. The ranking rule sorts the whole list of scored songs from highest to lowest score and returns the top k (default 5) songs. Scoring judges each song on its own; ranking compares them all and picks the winners.

- Potential biases I expect

Because this is a content-based system built on exact-match categories and hand-tuned weights, I expect a few biases:
- **Genre over-prioritization.** Genre is worth the most points (2.0) and is an exact-string match, so a song in the "wrong" genre can never earn those points even if it perfectly matches the user's mood, energy, and acoustic preference. For example, an `ambient` track that is genuinely chill and low-energy will always rank below a mediocre `lofi` track for a lofi-loving user. The system may ignore great songs that match the user's mood or feel but carry a different genre label.
- **Filter bubble / over-specialization.** By design it keeps recommending music that looks like what the user already said they want, so it rarely surprises the user or helps them discover new genres.
- **Popularity/representation bias in the catalog.** Genres with more songs (lofi has 3, pop has 2) have more chances to appear in the top results than genres with only one song, regardless of quality.
- **Rigid categories.** Exact-match on genre and mood means near-misses (e.g. "indie pop" vs "pop", or "chill" vs "relaxed") score zero, even though a human would consider them close.

I explore these further in the Limitations and Risks section and in the model card.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Below is the real terminal output from running `python -m src.main` with the default
`pop / happy` taste profile:

```
Loaded songs: 18

============================================================
 Top 5 recommendations for your taste profile
 genre=pop | mood=happy | target_energy=0.8 | likes_acoustic=False
============================================================

1. Sunrise City - Neon Echo
   Genre/Mood: pop / happy
   Score: 4.48 / 4.5
   Reasons:
     - genre match (pop) (+2.0)
     - mood match (happy) (+1.0)
     - energy closeness (song 0.82 vs target 0.80) (+0.98)
     - non-acoustic preference match (+0.5)

2. Gym Hero - Max Pulse
   Genre/Mood: pop / intense
   Score: 3.37 / 4.5
   Reasons:
     - genre match (pop) (+2.0)
     - energy closeness (song 0.93 vs target 0.80) (+0.87)
     - non-acoustic preference match (+0.5)

3. Rooftop Lights - Indigo Parade
   Genre/Mood: indie pop / happy
   Score: 2.46 / 4.5
   Reasons:
     - mood match (happy) (+1.0)
     - energy closeness (song 0.76 vs target 0.80) (+0.96)
     - non-acoustic preference match (+0.5)

4. City Pulse - Ray Verse
   Genre/Mood: hip hop / energetic
   Score: 1.50 / 4.5
   Reasons:
     - energy closeness (song 0.80 vs target 0.80) (+1.00)
     - non-acoustic preference match (+0.5)

5. Night Drive Loop - Neon Echo
   Genre/Mood: synthwave / moody
   Score: 1.45 / 4.5
   Reasons:
     - energy closeness (song 0.75 vs target 0.80) (+0.95)
     - non-acoustic preference match (+0.5)
```

Note how **Rooftop Lights** (ranked #3) matches the `happy` mood but is tagged
`indie pop`, so it misses the +2.0 genre points and ranks below the two `pop`
tracks. This is the "rigid categories" bias described above in action.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



