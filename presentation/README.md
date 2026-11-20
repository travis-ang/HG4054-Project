# HG4054 talk: "Are superstars more self-focused than role players?"

The slides for the 15-minute recorded talk, built as a full-screen web deck (Next.js 16 + Framer Motion).
22 slides in four "quarters" (the four parts the guidelines ask for), planned at 14:00 in total. **`TALK_SCRIPT.md`** is the talk script, nothing else: what to say on each slide, with `[click]` for each press of the right-arrow key. Timings, cue lines and checkpoints are in the Google Doc tab "Talk script"; the clock (T) uses those timings. Slides 6 to 9 introduce the main measure (Steps 18 and 19): counting "I" and "we" and its problems (6), the BERT setup and embeddings (7), the labelled data and the classifier (8), and what BERT finds plus the formula of the team-focused share (9). The audience is the lecturer, so slides use technical terms without explaining them; Travis explains them out loud. Slide 12 shows how the LDA question topics are built, on one real document (LeBron 2016, the slide 2 press conference): kept and removed words, the count vector, θ, and the choice of K (Step 22, `scripts/lda_method.py`). Slide 15 shows what reporters ask each tier (LDA topics, raw and with round and game day equal; Step 21, `scripts/lda_tiers.py`). Slide 21 is a fun fact added on 18 Nov (Step 20): the most and least team-focused players (`scripts/fun_fact.py`, descriptive).

## Run it

```bash
cd presentation
npm install          # first time only
npm run build && npx next start -p 3054
```

Open http://localhost:3054 in Chrome, press **F** for full screen.
(`npm run dev` also works while editing, but the built version runs smoother for recording.)

## Keys

| Key | Does |
|---|---|
| → / Space / PageDown / click | next build (each slide reveals step by step) |
| ← / PageUp | back one build |
| ↓ / ↑ | next / previous slide, skipping builds |
| Home / End | first / last slide |
| F | full screen |
| T | rehearsal clock (elapsed vs. planned time); hide it before recording |
| N | speaking prompts on screen (rehearsal only) |
| P | presenter window: prompts, clock, next slide, synced with the deck (put it on a second screen) |
| C | face-cam layout: the deck shrinks to the left 75% of the window |
| R | reset the clock |

The URL keeps your place (`#/slide/build`), so a reload stays on the same slide.

## Things to click or hover

Clicking these never moves the deck on (only clicks on empty space do). The prompts (N) list them as "Try:".

| Slide | Try |
|---|---|
| 1 Title | click the hoop to shoot again |
| 2 Guess | click a quote card to reveal who said it |
| 3 Predictions | click the I or WE ball to tip the seesaw |
| 5 Tiers | hover a face for the player's name |
| 6 Counting words | hover or click a problem for a real example |
| 7 BERT embeddings | hover or click a sentence for its cosine similarities |
| 8 Labels and classifier | hover or click a stage for its details (method, label shares, recall per class) |
| 9 What BERT finds | hover or click an example or a bar to light up that kind of "I" in every tier |
| 10 "We" check | hover or click a dot to read that real "we" sentence and how it was coded |
| 11 Like with like | hover or click a control to see what it does in the model |
| 12 How the topics are built | hover or click a word: why it was removed, or its most likely topic (from build 2); hover or click a K for its scores |
| 13 Main result | click No controls / All controls / Same player; hover a column for the CIs |
| 14, 16, 18 | hover a row, word or check for its numbers |
| 15 What reporters ask | hover or click a topic for its words, shares and both gaps |
| 17 Classifiers | hover a row for the CI; click a ball to roll it again |
| 21 Fun fact | hover or click a dot for that player's share |
| 22 Thank you | click the ball |

Cut on 18 Nov (Step 19, to keep words per slide down and the talk under 15 minutes): "Three more ways to look at the words" (the method now sits in the kickers of slides 16 and 17) and the old "What reporters ask" (raw topic shares only). Their components (`Lenses`, `Topics`) are still in `q2.tsx` / `q3.tsx`, unused. "What reporters ask" came back the same day as a new slide (`Questions`, Step 21; now slide 15) that also shows the gaps with round and game day held equal.

## Recording

- Hide the clock (T) and notes (N). Use the presenter window (P) on another screen if you have one.
- Face cam: either a small camera bubble in a corner, or press **C** and put the camera in the right-hand strip.
- Wait for each build to finish before talking over it; transitions take under a second.

## Where the numbers come from

Every number is read from `src/data/results.json`, which `scripts/export_site_data.py` (in the project's
`scripts/` folder) writes from the saved result files. Re-run it if any result changes:

```bash
cd scripts && python export_site_data.py
```

## Files

- `src/slides/q1.tsx` … `q4.tsx` (q2 holds `LdaMethod`, slide 12; q3 holds `Questions`, slide 15; q4 holds the fun fact, slide 21) and `bert.tsx` (slides 7 and 8): the slides, one function each; `src/slides/index.ts`: order, builds, timings, prompts
- `src/components/deck/`: stage scaling, court background, scoreboard header and progress bar, keyboard and presenter sync
- `src/components/ui.tsx`: shared pieces (titles, count-ups, quotes with "I"/"we" marked, headshots; `stop`, `Tap`, `usePick`, `Tip` for the clickable parts)
- `src/lib/theme.ts`: colours (basketball theme; tier colours validated) and number formatting
- `public/img/`: player headshots (NBA.com, 1040 × 760; `Headshot` in `ui.tsx` overrides Tailwind's `img { max-width: 100% }` so the face is centred in the circle) and press-conference photos (Wikimedia Commons; credited on the last slide)

Keep the site local: the NBA.com headshots are not licensed for publishing.
