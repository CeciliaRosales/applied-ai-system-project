# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**

It matches songs to a listener's vibe. The name says what it does in one word.

---

## 2. Intended Use  

**Goal / task.** VibeMatch takes a short taste profile and suggests songs from a small catalog. It guesses which songs a listener will like and ranks them best-first. It also gives a plain-English reason for each pick.

**Who it is for.** This is a classroom project. It is a learning tool, not a real app.

**What it assumes about the user.** It assumes the user can name one favorite genre, one favorite mood, a target energy level (0 to 1), and whether they like acoustic music.

**Intended use.**
- Learning how a simple recommender turns data into ranked suggestions.
- Exploring how changing weights or profiles changes the results.

**Non-intended use.**
- Do not use it for real music apps or real users.
- Do not use it to judge songs, artists, or genres as "good" or "bad."
- Do not trust it outside this tiny 18-song catalog.

---

## 3. How the Model Works  

Think of it like a points game. Every song starts with zero points. Then the song earns points for each way it matches what the listener asked for.

- Same genre as the listener's favorite: **+2 points**.
- Same mood: **+1 point**.
- Close to the listener's energy level: **up to +1 point**. A perfect match gets the full point. The bigger the gap, the fewer points. So it rewards being *close*, not just loud or quiet.
- Matches the listener's acoustic choice (acoustic or not): **+0.5 points**.

The most a song can get is **4.5 points**. After every song has a score, the model sorts them from most points to fewest and shows the top 5. Each pick comes with the list of reasons it earned points.

**Reliability layer (the applied-AI extension).** Around that core, three things now run inside the main recommendation path:

- **Input guardrail** (`validate_user_prefs): a taste profile is checked before scoring. Blank genre/mood, an energy value outside 0–1, a wrong-typed field, or a missing key is rejected and logged — the scorer never sees bad input.
- **Confidence** (confidence_from_score): each pick's raw 0–4.5 score is normalized to a 0–1 confidence, shown next to every recommendation.
- **Abstain** (is_confident): if the top pick's confidence is below 0.50, the system prints "no strong matches found" instead of presenting weak guesses as answers.

These are verified by a pytest suite and by an evaluation harness (src/evaluate.py) that reports PASS/FAIL for realistic, adversarial, and malformed profiles.

**What I changed from the starter.** The starter only had empty functions. I wrote the CSV loader, the scoring rule, and the ranking step, picked the weights (genre matters most, acoustic least), made the energy score reward closeness, and made each recommendation explain itself. For the final applied-AI version I added the reliability layer above:
validation guardrail, confidence scoring, the abstain rule, logging, and the test/eval harness.

---

## 4. Data  

The catalog is a small CSV file. It has **18 songs**.

Each song has 10 fields: id, title, artist, genre, mood, energy, tempo, valence, danceability, and acousticness. The last five are numbers. The  model only uses genre, mood, energy, and acousticness.

**Genres:** pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip hop, classical, edm, country, r&b, metal, folk, and reggae.
**Moods:** happy, chill, intense, relaxed, focused, moody, energetic, melancholic, romantic, aggressive, nostalgic, peaceful, and uplifting.

**What I changed.** The starter had 10 songs. I added 8 more to bring in new genres and moods (like classical, metal, folk, and reggae).

**What is missing.** The catalog is tiny. Most genres have only one song, so those tastes are barely covered. Energy values bunch up at the low and high ends, with little in the middle. There is nothing about lyrics, language, era, or culture. So a lot of real musical taste is left out.

---

## 5. Strengths  

It works well when the listener's taste clearly exists in the catalog. A pop-happy fan gets pop-happy songs. A lofi-chill fan gets calm lofi songs. Those results matched my gut feeling.

- **Clear tastes get clear results.** Well-matched profiles score near the top (4.5).
- **Opposite tastes stay separate.** The chill listener and the intense listener share no songs, which is exactly right.
- **Every pick is explained.** The model shows why each song was chosen. This makes it easy to trust or question a result.
- **Energy closeness works.** Picking songs near the target energy felt smarter than just picking the loudest or quietest.

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

One weakness I discovered during my experiments is that the way I calculate the "energy gap" quietly disadvantages listeners with moderate energy tastes. Energy is scored as 1 - |song_energy - target_energy|, so every song earns some energy points no matter how poor the fit, and the catalog's energy values are clustered at the extremes (7 songs sit at 0.24–0.42 and 8 songs at 0.75–0.97, but only 3 fall in the 0.55–0.60 middle). This means a user who wants very low or very high energy can always find a near-perfect match (closeness ≈ 1.0), while a mid-energy user's best possible match is structurally weaker and their top results end up separated by tiny, almost arbitrary differences. When I doubled the energy weight in my sensitivity test the effect grew: for users whose genre and mood did not match any song, the rankings were driven almost entirely by these small energy gaps, producing noisier and less meaningful recommendations. In short, the scoring favors users whose taste happens to sit where the data is dense, and underserves everyone in between.

Other limitations to explore further:

- Features it does not consider (valence, danceability, tempo, lyrics, language)
- Genres or moods that are underrepresented (every genre except lofi and pop has only one song)
- Cases where the system overfits to one preference (exact-match genre can override a better overall fit)
- Ways the scoring might unintentionally favor some users (mainstream/extreme-taste listeners over moderate or niche ones)

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

### Profiles I tested

I defined six taste profiles in src/main.py and ran python -m src.main, looking at the top-5 list and per-song score for each. Three were realistic listeners and three were deliberately "adversarial" edge cases meant to try to trick the scoring logic:

| # | Profile | genre / mood / target_energy / likes_acoustic | Top pick (score /4.5) |
|---|---------|-----------------------------------------------|-----------------------|
| P1 | High-Energy Pop | pop / happy / 0.9 / False | Sunrise City (4.42) |
| P2 | Chill Lofi | lofi / chill / 0.35 / True | Library Rain (4.50) |
| P3 | Deep Intense Rock | rock / intense / 0.9 / False | Storm Runner (4.49) |
| A1 | Conflicting Energy vs Mood | classical / melancholic / 0.95 / False | Winter Elegy (3.29) |
| A2 | Nonexistent Genre & Mood | k-pop / sad / 0.5 / True | Backroad Sunset (1.45) |
| A3 | Impossible Combo | metal / peaceful / 0.2 / True | Meadow Song (2.37) |

### What surprised me

- **The score ceiling is itself a quality signal.** Coherent profiles topped out near the 4.5 maximum (P2 hit a perfect 4.50), while broken profiles capped around 1.5. You can tell a profile is poorly matched just from how low its #1 score is.
- **The system never abstains.** With a genre and mood that don't exist in the catalog (A2), it still returned a confident top 5 built only from energy + acoustic. Its #1 pick (a country song) has nothing to do with "k-pop" or "sad."
- **Genre weighting can surface an actively wrong song.** In A3, an aggressive metal track (Iron Verdict) landed at #2 for a listener who asked for "peaceful, acoustic, low-energy" music — the exact opposite of what they wanted.
- **Mood crosses genres.** In P3, Gym Hero (a pop song) ranked #2 purely on the shared "intense" mood, confirming mood is a looser signal than genre.

### Pairwise comparisons

**Realistic vs realistic**
- **P1 vs P2:** High-Energy Pop fills its list with upbeat pop; Chill Lofi shifts entirely to low-energy acoustic lofi. The two top-5s share zero songs — exactly right, since their energy targets (0.9 vs 0.35), genres, and acoustic prefs are all opposite.
- **P1 vs P3:** Both want high energy and non-acoustic, so they share energetic filler (Gym Hero, Neon Overdrive appear in both), but P1's genre pull puts pop first while P3's puts rock first — same energy pool, different genre steering the #1.
- **P2 vs P3:** Polar opposites — P2 is calm acoustic lofi/ambient, P3 is loud non-acoustic rock/edm/metal, with no overlap. Validates that energy + acoustic cleanly separate low-key and high-intensity tastes.

**Realistic vs adversarial**
- **P1 vs A1:** P1 produces one coherent, high-scoring pop list; A1 (classical/melancholic but energy 0.95) yields a single genre+mood match (Winter Elegy 3.29) followed by a jumble of unrelated high-energy songs — conflicting prefs fragment the list.
- **P1 vs A2:** P1's genre/mood fire and produce a 4.42 top; A2's nonexistent labels never fire, so its top is only 1.45 — the score gap alone flags A2 as a bad match.
- **P1 vs A3:** Non-overlapping and mirror-imaged: A3's peaceful/acoustic/low-energy pull is the inverse of P1's, yet genre bias still floats a loud metal track high in A3.
- **P2 vs A1:** Both surface some acoustic songs, but A1's high energy target (0.95) makes its filler high-energy while P2's is low-energy — target_energy reshapes the tail.
- **P2 vs A2:** Revealing — they share songs (lofi tracks, Coffee Shop Stories) because both like acoustic, but P2 scores them ~4.5 while A2 scores the same songs ~1.4. Same songs, very different confidence, because A2 lacks any genre/mood match.
- **P2 vs A3:** Both prefer acoustic + low energy and both surface calm acoustic songs (Library Rain, Spacewalk Thoughts), but A3 additionally matches the "peaceful" mood (Meadow Song) that P2 doesn't — showing how one mood match reorders the top.
- **P3 vs A1:** Both have high-energy filler (Neon Overdrive, Gym Hero, Iron Verdict, Storm Runner all appear) because A1's 0.95 target overlaps P3's 0.9, but P3 earns a real genre+mood #1 (Storm Runner 4.49) while A1's #1 is a mismatched classical track.
- **P3 vs A2:** Opposite acoustic prefs (P3 non-acoustic, A2 acoustic) and different energy push their lists apart, so they barely overlap.
- **P3 vs A3:** Near-opposites (loud non-acoustic vs peaceful acoustic); their one shared song is the metal track Iron Verdict — which P3 legitimately ranks and A3 wrongly floats to #2 via genre bias. A clean illustration of genre over-prioritization.

**Adversarial vs adversarial**
- **A1 vs A2:** A1 lands one genuine match (Winter Elegy 3.29) while A2 tops out at 1.45 — a direct demo of how many rules can fire (2 vs 0) driving the achievable score.
- **A1 vs A3:** Both are conflicting profiles with opposite energy targets (0.95 vs 0.2), so their filler mirrors each other — A1's is high-energy, A3's is low-energy.
- **A2 vs A3:** Both like acoustic and surface calm acoustic songs, but A3's "peaceful" mood fires once (Meadow Song) and lifts it above A2's pure energy-only ranking — a single working signal is enough to change the #1.

Overall the outputs are **valid**: whenever a profile's preferences genuinely exist in the catalog, the right songs rise and the reasons explain why; the surprises all trace back to known limitations (rigid exact-match categories, no abstain threshold, genre over-weighting) rather than to bugs in the scoring math.

---

## 8. Future Work  

If I kept building this, I would try:

1. **Soft category matching.** Right now genre and mood must match exactly. "indie pop" should count as close to "pop." I would give partial points for similar labels.
2. **Refuse, don't just warn.** The abstain rule now *flags* low-confidence results with a "no strong matches found" banner, but it still shows the weak guesses. A stricter product would return an empty list (or ask the user to broaden their taste) below the threshold.
3. **More features and more data.** I would use tempo, valence, and danceability too, and add many more songs, especially mid-energy songs and more per genre. This would make the results fairer and more varied.

---

## 9. Personal Reflection  

**Biggest learning moment.** My biggest lesson was that the weights *are* the opinion. Choosing genre = 2 and mood = 1 was not just a number choice. It decided who the system serves and who it ignores. Small numbers had big effects.

**How AI tools helped, and when I double-checked.** AI tools helped me move fast. They helped me test edge cases and figure out the logic for the scoring code. But I still had to check them. For example, my run file and my scoring code used different key names, so nothing matched at first. I also had to catch when a claimed song count did not match the real data. The AI was a strong helper, not a source of truth.

**What surprised me.** I was surprised that such simple rules could "feel" like real recommendations. There is no learning and no AI brain inside. It is just points and sorting. But the ranked list with reasons still felt smart and personal.

**What I would try next.** I would add soft matching for similar genres, turn the abstain warning into a real refusal, and add more songs and features. I would also test many more listener types to find where the system is unfair.

---

## 10. Responsible AI Reflection

### What are the limitations or biases in your system?

The biggest biases are **genre over-prioritization** (an exact-match genre worth 2.0 points can outrank a song that fits the user better on every other axis), **rigid categories** ("indie pop" scores zero against "pop"), **catalog representation bias** (genres with more songs get recommended more often), and an **energy-scoring bias** that gives near-perfect matches to listeners at the extremes while underserving mid-energy tastes, because the catalog's energy values cluster at the ends. See Section 6 for the detailed analysis. The system is also limited to a tiny 18-song catalog and ignores lyrics, language, era, and culture.

### Could your AI be misused, and how would you prevent that?

Even a toy recommender can be misused. Two concrete risks:

1. **False authority / over-trust.** The confidence number and the "reasons" make outputs look objective, so someone could present VibeMatch's ranking as evidence that one artist or genre is "better" than another, when it only measures fit to a hand-tuned rule on a tiny catalog. *Prevention:* the model card's Non-intended-use section says explicitly not to use it to judge songs/artists as good or bad, and the abstain banner plus visible confidence scores actively discourage trusting weak results.
2. **Manipulating what people hear.** Because *the weights are the opinion*, whoever sets them decides whose taste is served — the same lever a real platform could use to quietly push certain genres. *Prevention:* keeping the weights, the data, and the scoring logic fully transparent and version-controlled (they're constants in recommender.py, not a hidden black box) means any such tilt is inspectable and reviewable rather than opaque.

### What surprised you while testing your AI's reliability?

Two things. First, **the top score is itself a reliability signal** — coherent profiles top out near 4.5 (confidence ≈ 1.0) while impossible ones cap around 1.5 (≈ 0.32), so you can tell a bad match just from the number. That's what made a single confidence threshold a workable abstain rule. Second, **the base system never admitted uncertainty**: with a genre and mood that don't exist in the catalog it still returned a confident-looking top 5 built from weak signals. Watching it confidently recommend a country song to a "k-pop / sad" listener is what convinced me the abstain guardrail was necessary, not optional.

### Collaboration with AI: one helpful suggestion, one flawed one

I built this with assitance from Claude. 

- **Helpful suggestion.** When I described the "it never abstains" problem, the AI proposed normalizing the existing 0–4.5 score into a 0–1 confidence and wiring a threshold check into the *main* path (not a side script), so the fix actually changed behavior and was testable. That framing — reuse the score I already compute rather than invent a new signal — is exactly what made the reliability layer small and coherent.
- **Flawed suggestion.** 
There were snippets of code that the AI would suggest that would not import the necessary items. Like for validate_user_prefs, the AI called logging.warning(...) but it never imported logging which would have brought up an error. Luckily, I was able to catch the error, import the missing import, and fix it. 

