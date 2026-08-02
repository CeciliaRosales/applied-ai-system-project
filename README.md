# 🎵 VibeMatch — Applied AI System

## Base Project (Modules 1–3)

This project extends my **Module 1–3 "Music Recommender Simulation"** mini-project. The
original was a small content-based recommender: it represented songs and a user "taste
profile" as data, applied a hand-designed additive scoring rule to rank songs, and
printed a top-5 list. Its goal was to show how a simple points-and-sorting rule can
behave like a real recommendation engine, and to reflect on where bias creeps in.

## Project Summary

**VibeMatch** takes that recommender and wraps it in a **reliability layer** so it behaves
like a trustworthy applied AI system rather than a demo. You describe your taste with four
things — a favorite genre, a favorite mood, a target energy level (0–1), and whether you
like acoustic music — and the system:

1. **validates** your profile (a guardrail that rejects malformed input instead of crashing),
2. **scores and ranks** all 18 songs in the catalog,
3. attaches a **0–1 confidence** to every pick, and
4. **abstains** — prints *"no strong matches found"* — when even its best pick is weak,
   instead of confidently presenting junk.

Every pick still comes with a plain-English reason. A separate **evaluation harness**
(`src/evaluate.py`) and a **pytest suite** prove these behaviors automatically.

### Required AI feature: Reliability / Testing System

This system is deterministic (points-and-sort, no LLM), so its integrated AI feature is a
**Reliability / Testing System**. It is not a bolt-on script — the guardrail, confidence
scoring, and abstain rule run **inside the main recommendation path** in
[`src/main.py`](src/main.py) and meaningfully change the output (bad profiles are rejected;
low-confidence results are flagged). Reliability is then *measured* by
[`src/evaluate.py`](src/evaluate.py) and [`tests/test_recommender.py`](tests/test_recommender.py).

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

## Architecture Overview

The system diagram lives as a Mermaid source file at
[`diagrams/architecture.mmd`](diagrams/architecture.mmd) (paste it into
[mermaid.live](https://mermaid.live) to render). Data flows left to right:

**Input → Guardrail → Score → Rank → Confidence/Abstain → Output**, with a testing/human
review lane checking the pipeline.

- **Input.** A user taste profile plus the song catalog (`data/songs.csv`).
- **Guardrail** — `validate_user_prefs` (in [`src/recommender.py`](src/recommender.py)):
  rejects malformed profiles (blank genre, out-of-range energy, wrong types, missing keys)
  *before* they reach the scorer, and logs the rejection.
- **Score & rank** — `score_song` / `recommend_songs`: additive weighting
  (genre 2.0 > mood 1.0 = energy-max 1.0 > acoustic 0.5), then sort and take the top *k*.
- **Confidence & abstain** — `confidence_from_score` normalizes the 0–4.5 score to 0–1;
  `is_confident` compares the top pick to a 0.50 threshold and triggers the abstain banner
  when nothing matches well.
- **Output** — `src/main.py` prints the ranked list with reasons and confidence, or a
  rejection / abstain message.
- **Checks** — `tests/test_recommender.py` (pytest) and `src/evaluate.py` (a PASS/FAIL
  harness) verify the guardrail, confidence, and abstain behaviors; the experiments in this
  README and `model_card.md` are the human-review lane.

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

3. Run the app (prints top-5 recommendations for every taste profile):

```bash
python -m src.main
```

4. Run the evaluation harness (PASS/FAIL reliability report + confidence summary):

```bash
python -m src.evaluate
```

### Running Tests

```bash
pytest
```

The suite (`tests/test_recommender.py`) covers the scoring/ranking logic **and** the
reliability layer: input validation, confidence bounds/monotonicity, the abstain
threshold, and the nonexistent-taste case.

---

## Sample Recommendation Output

Below are three reproducible end-to-end runs demonstrating (1) a normal high-confidence
result, (2) the abstain guardrail, and (3) the input-validation guardrail. All are real
output from the current code.

### Example 1 — Normal run, high confidence (`python -m src.main`)

Input profile: `genre=pop, mood=happy, target_energy=0.9, likes_acoustic=False`.

```
Loaded songs: 18

============================================================
 High-Energy Pop - Top 5
 genre=pop | mood=happy | target_energy=0.9 | likes_acoustic=False
============================================================

1. Sunrise City - Neon Echo
   Genre/Mood: pop / happy
   Score: 4.42 / 4.5   Confidence: 0.98
   Reasons:
     - genre match (pop) (+2.0)
     - mood match (happy) (+1.0)
     - energy closeness (song 0.82 vs target 0.90) (+0.92)
     - non-acoustic preference match (+0.5)

2. Gym Hero - Max Pulse
   Genre/Mood: pop / intense
   Score: 3.47 / 4.5   Confidence: 0.77
   Reasons:
     - genre match (pop) (+2.0)
     - energy closeness (song 0.93 vs target 0.90) (+0.97)
     - non-acoustic preference match (+0.5)

3. Rooftop Lights - Indigo Parade
   Genre/Mood: indie pop / happy
   Score: 2.36 / 4.5   Confidence: 0.52
   Reasons:
     - mood match (happy) (+1.0)
     - energy closeness (song 0.76 vs target 0.90) (+0.86)
     - non-acoustic preference match (+0.5)
```

Note how **Rooftop Lights** (#3) matches the `happy` mood but is tagged `indie pop`, so it
misses the +2.0 genre points and ranks below the two `pop` tracks (the "rigid categories"
bias). Its confidence of **0.52** is barely above the abstain line — the system signals
that this is a much weaker match than the 0.98 top pick.

### Example 2 — Abstain guardrail fires (nonexistent taste)

Input profile: `genre=k-pop, mood=sad, target_energy=0.5, likes_acoustic=True`. Neither
`k-pop` nor `sad` exists in the catalog, so no categorical rule can fire. Instead of
bluffing, the system flags the whole result as low-confidence:

```
============================================================
 Adversarial: Nonexistent Genre & Mood - Top 5
 genre=k-pop | mood=sad | target_energy=0.5 | likes_acoustic=True
============================================================

 [!] No strong matches found (top confidence 0.32 < 0.50).
     Showing best-effort guesses only; treat these as low-confidence.

1. Backroad Sunset - Cody Lane
   Genre/Mood: country / nostalgic
   Score: 1.45 / 4.5   Confidence: 0.32
   Reasons:
     - energy closeness (song 0.55 vs target 0.50) (+0.95)
     - acoustic preference match (+0.5)
```

The corresponding log line (stderr):

```
[WARNING] vibematch.main: Abstain for profile 'Adversarial: Nonexistent Genre & Mood': top confidence 0.32 below threshold 0.50
```

### Example 3 — Input-validation guardrail rejects bad input

The guardrail runs before scoring. A profile with a blank genre and an out-of-range energy
is rejected (and logged) instead of crashing the scorer:

```
============================================================
 (bad profile) - Top 5
============================================================
 [REJECTED] Invalid taste profile:
   - favorite_genre must be a non-empty string.
   - target_energy must be a number between 0 and 1.
```
```
[WARNING] vibematch: Rejected invalid user preferences: ['favorite_genre must be a non-empty string.', 'target_energy must be a number between 0 and 1.']
```

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
- **The system used to never abstain.** With no valid matches (profile 5) the base scorer
  still returned a confident top 5 built from weak signals. **This finding directly
  motivated the abstain guardrail** now in the system: when the top pick's confidence is
  below 0.50, the system prints *"no strong matches found"* (see Example 2 above).
- **Genre weighting can surface actively wrong songs** (Iron Verdict at #2 for a "peaceful
  acoustic" listener), reinforcing the genre-over-prioritization bias noted above.

---

## Testing Summary

Reliability is verified two ways. Both are reproducible from the commands in *Getting
Started*.

**1. Unit tests — `pytest` (11 passed).** The suite covers scoring/ranking and the whole
reliability layer: validation accepts good input and rejects blank genre, out-of-range
energy, a bool passed as energy, and missing keys; confidence stays in [0,1] and is
monotonic; the abstain threshold behaves; and a nonexistent taste yields a low-confidence
(abstaining) top pick.

**2. Evaluation harness — `python -m src.evaluate` (8/8 passed).** Runs a battery of
realistic, adversarial, and malformed profiles and asserts the expected reliability
behavior for each:

```
========================================================================
 VibeMatch Evaluation Harness  (18 songs, abstain threshold = 0.50)
========================================================================
RESULT  EXPECTATION      CASE                       DETAIL
------------------------------------------------------------------------
PASS    valid_confident  High-Energy Pop            top='Sunrise City' conf=0.98
PASS    valid_confident  Chill Lofi                 top='Library Rain' conf=1.00
PASS    valid_confident  Deep Intense Rock          top='Storm Runner' conf=1.00
PASS    valid_abstain    Nonexistent Genre & Mood   abstained conf=0.32
PASS    invalid          Blank genre                rejected (1 error(s))
PASS    invalid          Energy out of range        rejected (1 error(s))
PASS    invalid          Missing likes_acoustic     rejected (1 error(s))
PASS    invalid          likes_acoustic wrong type  rejected (1 error(s))
------------------------------------------------------------------------
Summary: 8/8 cases passed | avg top-confidence (scored cases) = 0.82
All reliability checks passed: guardrail, confidence, and abstain all behaved as expected.
========================================================================
```

**What worked / what didn't / what I learned.** All 11 unit tests and all 8 harness cases
pass. Coherent tastes score near the 4.5 ceiling (confidence ≈ 0.98–1.00); tastes absent
from the catalog correctly abstain (confidence 0.32). What *didn't* work in the base
system — silently returning confident junk for impossible tastes, and crashing on
malformed input (a `logging` `NameError` in the original `validate_user_prefs`) — is
exactly what the reliability layer now catches. The main lesson: a recommender's *score*
is only trustworthy once you also decide **when not to trust it**, which is what the
confidence threshold encodes.

---

## Limitations and Risks

  - It only works on a tiny 18-song catalog, so results are shallow
  - Genre and mood must match exactly, so "indie pop" never counts as "pop"
  - Most genres have only one song, so niche tastes can't fill a good top-5
  - It now flags low-confidence results ("no strong matches found"), but it still *shows*
    the weak guesses rather than returning an empty list — a stricter product might refuse
    entirely below the threshold
  - It ignores lyrics, language, tempo, and culture, so it misses a lot of what makes music feel right
  - The energy score quietly favors people with very high or very low energy taste, and underserves middle-of-the-road listeners

---

## Reflection

> My **graded responsible-AI reflection** — AI collaboration (one helpful and one flawed
> suggestion), biases, and testing surprises — is in [**`model_card.md`**](model_card.md).
> The note below is a short portfolio summary.

Building this showed me that a recommendation is really just math on data. Each song becomes a set of numbers and labels, the system scores how well each one matches the user, and "prediction" is just sorting by that score. There's no magic - the ranked list only feels personal because the scoring rule lines up with what the user said they wanted. Extending it into an applied system taught me the other half: a score is only useful once you also decide *when not to trust it*, which is why the confidence threshold and abstain rule matter as much as the scoring.

It also showed me how easily bias sneaks in. The weights I chose decided whose taste the system serves best, and the data itself was unfair: genres with more songs got recommended more, and listeners with "average" energy got weaker matches than people at extremes. In a real app, those small choices would quietly shape what millions of people hear.

## What this project says about me as an AI engineer

I take a prototype and make it *trustworthy*: I found and fixed a real crash in the input
validator, wired guardrails and confidence into the main path so the behavior actually
changes, and backed every claim with a reproducible test harness. I care as much about how
a system fails and admits uncertainty as about its happy path.


