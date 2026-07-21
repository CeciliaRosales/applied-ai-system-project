# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

VibeMatch 1.0 is a small content-based music recommender. You describe your taste with four things - a favorite genre, a favorite mood, a target energy level, and whether you like acoustic music - and it scores all 18 songs in the catalog, then shows the top 5 with a plain - English reason for each pick. It's a learning project that shows how a simple points-and-sorting rule can behave like a real recommendation engine.

---

## How The System Works

My music recommender is a content-based system. It matches songs to a user by comparing the attributes of each song against the user's stated taste, then ranks the best matches. It works in two steps: score every song, then rank the scored list.

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
   ```

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

Running `python -m src.main` prints the top 5 for each of six taste profiles (see the
Experiments section below for all of them). Here is the first profile's real output,
**High-Energy Pop**:

```
Loaded songs: 18

============================================================
 High-Energy Pop - Top 5
 genre=pop | mood=happy | target_energy=0.9 | likes_acoustic=False
============================================================

1. Sunrise City - Neon Echo
   Genre/Mood: pop / happy
   Score: 4.42 / 4.5
   Reasons:
     - genre match (pop) (+2.0)
     - mood match (happy) (+1.0)
     - energy closeness (song 0.82 vs target 0.90) (+0.92)
     - non-acoustic preference match (+0.5)

2. Gym Hero - Max Pulse
   Genre/Mood: pop / intense
   Score: 3.47 / 4.5
   Reasons:
     - genre match (pop) (+2.0)
     - energy closeness (song 0.93 vs target 0.90) (+0.97)
     - non-acoustic preference match (+0.5)

3. Rooftop Lights - Indigo Parade
   Genre/Mood: indie pop / happy
   Score: 2.36 / 4.5
   Reasons:
     - mood match (happy) (+1.0)
     - energy closeness (song 0.76 vs target 0.90) (+0.86)
     - non-acoustic preference match (+0.5)

4. Storm Runner - Voltline
   Genre/Mood: rock / intense
   Score: 1.49 / 4.5
   Reasons:
     - energy closeness (song 0.91 vs target 0.90) (+0.99)
     - non-acoustic preference match (+0.5)

5. Neon Overdrive - Pulse Theory
   Genre/Mood: edm / energetic
   Score: 1.45 / 4.5
   Reasons:
     - energy closeness (song 0.95 vs target 0.90) (+0.95)
     - non-acoustic preference match (+0.5)
```

Note how **Rooftop Lights** (ranked #3) matches the `happy` mood but is tagged
`indie pop`, so it misses the +2.0 genre points and ranks below the two `pop`
tracks. This is the "rigid categories" bias described above in action.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

I defined six taste profiles in `src/main.py` and ran `python -m src.main` to see how
the recommender behaves for each. The first three are realistic listeners; the last
three are deliberately **adversarial** edge cases designed to try to "trick" the
scoring logic.

### Realistic profiles

**1. High-Energy Pop** — behaves as expected: the two `pop` tracks lead, and the
`indie pop / happy` track ranks below them (rigid-category bias again).

```
============================================================
 High-Energy Pop - Top 5
 genre=pop | mood=happy | target_energy=0.9 | likes_acoustic=False
============================================================

1. Sunrise City - Neon Echo         Score: 4.42 / 4.5  (genre+mood+energy 0.92+acoustic)
2. Gym Hero - Max Pulse             Score: 3.47 / 4.5  (genre+energy 0.97+acoustic)
3. Rooftop Lights - Indigo Parade   Score: 2.36 / 4.5  (mood+energy 0.86+acoustic; indie pop misses genre)
4. Storm Runner - Voltline          Score: 1.49 / 4.5  (energy 0.99+acoustic only)
5. Neon Overdrive - Pulse Theory    Score: 1.45 / 4.5  (energy 0.95+acoustic only)
```

**2. Chill Lofi** — the ideal case: Library Rain scores a **perfect 4.50 / 4.5**.
The three lofi tracks lead, then the chill ambient track.

```
============================================================
 Chill Lofi - Top 5
 genre=lofi | mood=chill | target_energy=0.35 | likes_acoustic=True
============================================================

1. Library Rain - Paper Lanterns    Score: 4.50 / 4.5  (genre+mood+energy 1.00+acoustic)
2. Midnight Coding - LoRoom          Score: 4.43 / 4.5  (genre+mood+energy 0.93+acoustic)
3. Focus Flow - LoRoom               Score: 3.45 / 4.5  (genre+energy 0.95+acoustic; mood is "focused")
4. Spacewalk Thoughts - Orbit Bloom  Score: 2.43 / 4.5  (mood+energy 0.93+acoustic; ambient misses genre)
5. Coffee Shop Stories - Slow Stereo Score: 1.48 / 4.5  (energy 0.98+acoustic only)
```

**3. Deep Intense Rock** — Storm Runner wins (4.49); note Gym Hero (`pop / intense`)
ranks #2 purely on the shared `intense` mood, showing how mood crosses genres.

```
============================================================
 Deep Intense Rock - Top 5
 genre=rock | mood=intense | target_energy=0.9 | likes_acoustic=False
============================================================

1. Storm Runner - Voltline          Score: 4.49 / 4.5  (genre+mood+energy 0.99+acoustic)
2. Gym Hero - Max Pulse             Score: 2.47 / 4.5  (mood+energy 0.97+acoustic; pop misses genre)
3. Neon Overdrive - Pulse Theory    Score: 1.45 / 4.5  (energy 0.95+acoustic only)
4. Iron Verdict - Ashfall           Score: 1.43 / 4.5  (energy 0.93+acoustic only)
5. Sunrise City - Neon Echo         Score: 1.42 / 4.5  (energy 0.92+acoustic only)
```

### Adversarial / edge-case profiles

**4. Conflicting Energy vs Mood** (`classical` + `melancholic`, but `target_energy=0.95`).
Melancholic classical music is inherently low-energy, so the mood/genre pull fights the
high-energy request. **Result: genre + mood win decisively.** Winter Elegy tops the list
(3.29) despite an energy match of only 0.29 — the +3.0 of categorical points swamps the
near-zero energy score. The stated energy preference is effectively ignored.

```
============================================================
 Adversarial: Conflicting Energy vs Mood - Top 5
 genre=classical | mood=melancholic | target_energy=0.95 | likes_acoustic=False
============================================================

1. Winter Elegy - Anna Vireo        Score: 3.29 / 4.5  (genre+mood, but energy only 0.29)
2. Neon Overdrive - Pulse Theory    Score: 1.50 / 4.5  (energy 1.00+acoustic only)
3. Gym Hero - Max Pulse             Score: 1.48 / 4.5  (energy 0.98+acoustic only)
4. Iron Verdict - Ashfall           Score: 1.48 / 4.5  (energy 0.98+acoustic only)
5. Storm Runner - Voltline          Score: 1.46 / 4.5  (energy 0.96+acoustic only)
```

**5. Nonexistent Genre & Mood** (`k-pop` + `sad`, neither of which exists in the catalog).
The genre and mood rules can **never** fire, yet the system still confidently returns 5
songs — ranked purely on energy closeness + acoustic. **The top pick (a country song about
a sunset) has nothing to do with "k-pop" or "sad."** This exposes a real risk: the
recommender never says "no good matches," it silently falls back to weak signals.

```
============================================================
 Adversarial: Nonexistent Genre & Mood - Top 5
 genre=k-pop | mood=sad | target_energy=0.5 | likes_acoustic=True
============================================================

1. Backroad Sunset - Cody Lane      Score: 1.45 / 4.5  (energy 0.95+acoustic only)
2. Midnight Coding - LoRoom          Score: 1.42 / 4.5  (energy 0.92+acoustic only)
3. Focus Flow - LoRoom               Score: 1.40 / 4.5  (energy 0.90+acoustic only)
4. Coffee Shop Stories - Slow Stereo Score: 1.37 / 4.5  (energy 0.87+acoustic only)
5. Library Rain - Paper Lanterns    Score: 1.35 / 4.5  (energy 0.85+acoustic only)
```

**6. Impossible Combo** (`metal` + `peaceful` + `likes_acoustic=True` + `target_energy=0.2`).
Genre pulls toward loud, aggressive, high-energy metal while every other field wants the
opposite. **Result: a near-miss that is very revealing.** A folk song wins (2.37) on
mood + energy + acoustic — but the aggressive metal track (Iron Verdict, energy 0.97) still
lands at **#2** on genre points alone, despite being the exact opposite of "peaceful,
acoustic, low-energy." Genre weighting nearly recommended the least appropriate song.

```
============================================================
 Adversarial: Impossible Combo (peaceful acoustic metal) - Top 5
 genre=metal | mood=peaceful | target_energy=0.2 | likes_acoustic=True
============================================================

1. Meadow Song - The Willow Trio    Score: 2.37 / 4.5  (mood+energy 0.87+acoustic; folk misses genre)
2. Iron Verdict - Ashfall           Score: 2.23 / 4.5  (genre only, energy 0.23, no acoustic)
3. Winter Elegy - Anna Vireo        Score: 1.46 / 4.5  (energy 0.96+acoustic only)
4. Spacewalk Thoughts - Orbit Bloom  Score: 1.42 / 4.5  (energy 0.92+acoustic only)
5. Library Rain - Paper Lanterns    Score: 1.35 / 4.5  (energy 0.85+acoustic only)
```

### What the adversarial tests taught me

- **Categorical points dominate numeric ones.** When genre + mood (up to 3.0) conflict
  with energy (max 1.0), the labels win — so a strongly-stated energy preference can be
  overridden, for better (profile 4) or worse (profile 6).
- **The system never abstains.** With no valid matches (profile 5) it still returns a
  confident top 5 built from weak signals. A production system would need a minimum-score
  threshold or a "no strong matches found" message.
- **Genre weighting can surface actively wrong songs** (Iron Verdict at #2 for a "peaceful
  acoustic" listener), reinforcing the genre-over-prioritization bias noted above.

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

  - It only works on a tiny 18-song catalog, so results are shallow
  - Genre and mood must match exactly, so "indie pop" never counts as "pop"
  - Most genres have only one song, so niche tastes can't fill a good top-5
  - It never says "no good match" - it always returns 5 songs, even for tastes that don't exist in the data
  - It ignores lyrics, language, tempo, and culture, so it misses a lot of what makes music feel right
  - The energy score quietly favors people with very high or very low energy taste, and underserves middle-of-the-road listeners 

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this
Building this showed me that a recommendation is really just math on data. Each song becomes a set of numbers and labels, the system scores how well each one matches the user, and "prediction" is just sorting by that score. There's no magic - the ranked list only feels personal because the scoring rule lines up with what the user said they wanted.
It also showed me how easily bias sneaks in. The weights I chose decided whose taste the system serves best, and the data itself was unfair: genres with more songs got recommended more, and listeners with "average" energy got weaker matches than people at extremes. In a real app, those small choices would quietly shape what millions of people hear. 


