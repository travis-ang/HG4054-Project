import { BertLabels, WhatBert } from "./bert";
import { Hook, Predictions, TitleSlide } from "./q1";
import { LdaMethod, LikeWithLike, Measure, Pipeline, Tiers, WeCheck } from "./q2";
import { Classifiers, InContext, MainResult, Questions, Robustness, Situation, Words } from "./q3";
import { Credits, FinalScore, FunFact, Limits } from "./q4";
import { Pos, SlideDef } from "./types";

/** Order, builds (clicks), planned seconds (total 14:00, matching presentation/TALK_SCRIPT.md, 19 Nov) and speaking prompts ("Try:" = things to click or hover on the slide).
 *  Step 19 (18 Nov): added "What is BERT?" and "The new data"; cut "Three more ways" (Lenses) and "What reporters ask" (Topics);
 *  their components stay in q2.tsx / q3.tsx, unused. Step 21: "What reporters ask" back as Questions (LDA gaps).
 *  Step 22: "How the topics are built" (LdaMethod) after "Comparing like with like"; 22 slides. */
export const SLIDES: SlideDef[] = [
  { id: "title", quarter: 0, title: "Title", steps: 1, seconds: 15, Comp: TitleSlide,
    notes: ["Hi, I'm Travis.", "One question: are superstars more self-focused than role players?", "Measured through “I” and “we” in what players tell reporters.", "Try: click the hoop to shoot again."] },
  { id: "hook", quarter: 1, title: "Guess: superstar or role player?", steps: 3, seconds: 35, Comp: Hook,
    notes: ["Ask the viewer to guess.", "Click: light up the pronouns. Click: reveal (LeBron all “we”, Livingston all “I”).", "Opposite of the stereotype, but hand-picked, so: all 37,017 answers.", "Try: click a card to reveal who said it before the reveal click."] },
  { id: "predictions", quarter: 1, title: "Two opposite predictions", steps: 3, seconds: 45, Comp: Predictions,
    notes: ["Common belief: spotlight → self-focus → more “I”.", "Click: lab studies (Kacewicz 2014) say the reverse; status was relative to others in the room.", "Click: why care: if pronouns track status, text alone could hint at who holds power; this tests whether a lab finding holds in public, unscripted, high-stakes speech. Why NBA: status is public and objective.", "Prediction: superstars more “we”, tested both ways.", "Try: click the I or WE ball to tip the seesaw."] },
  { id: "pipeline", quarter: 2, title: "From transcripts to data points", steps: 4, seconds: 45, Comp: Pipeline,
    notes: ["So how do you measure this? Start with the data.", "Click through: ASAP Sports transcripts 2004–2026, scraped myself; moderator lines and coaches removed (coaches aren't on the ladder); 99.5% of answers matched to an NBA player (nba_api).", "Unit = one player in one press conference, answers summed: 4,425 units, 377 players.", "Why this data: status is public (All-Star, starts) and every player faces the same format."] },
  { id: "tiers", quarter: 2, title: "Three tiers of status", steps: 3, seconds: 40, Comp: Tiers,
    notes: ["Tier set each season: All-Star → superstar; else starter if started ≥ half the games; else role player.",
      "Click: counts and faces.", "Click: 86 players change tier (Draymond). Superstars talk more and more of their units are post-game → controls.", "Try: hover a face to see the player's name."] },
  { id: "measure", quarter: 2, title: "Counting words misses the meaning", steps: 3, seconds: 45, Comp: Measure,
    notes: ["The obvious measure: count “I” and “we”. Real Kobe answer.", "Click: 2 and 2 → 0.50, for an answer all about the team.", "Click: three problems: “I mean” (38% of “I”), “not about me”, non-team “we” → read each word in context.", "Try: hover a problem for a real example."] },
  { id: "bert", quarter: 2, title: "BERT embeddings", steps: 3, seconds: 45, Comp: WhatBert,
    notes: ["Why: counting can't tell “I mean” from “I scored”. Setup: bert-base-uncased, frozen; mean of last 4 layers per token; full answer as context; every “I” and “we” the we-share counts.", "Click: same token, different vectors, depending on the sentence.", "Click: nearest neighbours by cosine share the use (Kawhi's “not about me” → LeBron's, 0.84), so a linear classifier on the vectors should separate the uses.", "Try: hover or click a sentence for its cosine similarities."] },
  { id: "labels", quarter: 2, title: "Labels and classifier", steps: 3, seconds: 55, Comp: BertLabels,
    notes: ["720 uses: 300 random + 60 targeted per pronoun; a blind AI coder labels them from the text alone (“I”: self / team / conversation; “we”: team / not).", "Click: L2 logistic regression on the standardised 768-d vectors, C tuned by 5-fold CV grouped by player (no player in both train and test): accuracy 0.90 vs 0.60 majority. Then it labels all 111,278 “I”.", "Click: second blind AI coder: κ 1.00 on random uses, 0.65 on targeted “I”. My own blind check of the 100 random uses: “we” 92%, “I” 66% (κ 0.43), 62% against the classifier. Most “I” splits are framing verbs like “I think”; some were my slips, some are ambiguous, and one credit-giving “me” is a classifier miss. The AI coders agree with each other more than with a person. Bar set before: “I” passes, “we” fails → every “we” = team.", "Try: hover a stage for the details."] },
  { id: "context", quarter: 2, title: "What BERT finds", steps: 3, seconds: 45, Comp: InContext,
    notes: ["Counting calls all of these self-focus; BERT reads self, conversation, team. It still misses Kobe's “me”: say so.",
      "Click: 38% of all “I” is just conversation, about the same in every tier.",
      "Click: the main measure: team-focused share. Made the main measure after a first analysis; both measures agree.",
      "Try: hover or click an example or a bar to light up that kind of “I” in every tier."] },
  { id: "wecheck", quarter: 2, title: "Does “we” mean the team?", steps: 2, seconds: 25, Comp: WeCheck,
    notes: ["30 random uses per tier, read in context: about 9 in 10 are the team in every tier.", "Click: coded twice, 94% agreement, both AI. BERT couldn't beat calling every “we” team, so every “we” counts as team.", "Try: hover or click any dot to read that real “we” sentence and how it was coded."] },
  { id: "likewithlike", quarter: 2, title: "Comparing like with like", steps: 3, seconds: 45, Comp: LikeWithLike,
    notes: ["Question: does status go with team-focused share once we compare like with like?", "Click: six things that also go with pronoun use and differ by tier. One of them is the topic of the reporters' questions, from LDA: how that works is the next slide.", "Click: binomial GLM (logit): team words out of self + team words, because it's a count out of a total; SEs clustered by player (players appear many times). Player fixed effects: within the same player across seasons.", "Try: hover or click a control to see what it does in the model."] },
  { id: "lda", quarter: 2, title: "How the question topics are built", steps: 3, seconds: 50, Comp: LdaMethod,
    notes: ["How the topic controls are built. One document = all questions to one player in one press conference; here LeBron, 2016 Game 6, the press conference of the slide 2 quote. Lowercase; drop stop words, filler and 946 name words; plurals to singular; words and two-word phrases in at least 10 and at most half of the documents: 3,263 terms, raw counts.",
      "Click: LDA with K = 10, α = η = 1/K, batch variational Bayes. Each topic is a distribution over terms (φ), each document a mix of topics (θ). Each word is coloured by its most likely topic in this document. This one is 66% championship and legacy, 26% season run. The ten shares go into the GLM as controls.",
      "Click: K from 5 to 20, three seeds each, scored by NPMI coherence of the top words and by stability across seeds. K = 5 scores higher but merges themes; K = 10 has the highest coherence of 8 to 15 and every topic can be named. K = 5 is rerun as a robustness check.",
      "Try: hover a word to see why it was dropped or which topic it goes to; hover a K for its scores."] },
  { id: "main", quarter: 3, title: "Main result", steps: 4, seconds: 60, Comp: MainResult,
    notes: ["So, does status show up? Scoreboard: about 65% team-focused in every tier.", "Click: same with no controls, all controls, and within the same player.", "Click: superstar − role −0.5 points, CI −4.5 to +3.6; same player +0.9.", "Click: rules out gaps beyond about 4.5 points (0.2 SD), not smaller ones. Prediction not supported.", "Try: click No controls / All controls / Same player to put that model on the scoreboard; hover a column for the CIs."] },
  { id: "situation", quarter: 3, title: "Situation vs status", steps: 3, seconds: 40, Comp: Situation,
    notes: ["Same model, other variables: after a win about 9 points less team-focused; round and question wording go with shifts too.", "More “you” in the question goes with more “I” in the answer, which is why the question controls are in.", "Click: status is the smallest shift.", "Click: fans say “we” after wins (Cialdini); players are more team-focused after losses. Different measures.", "Try: hover a row for its 95% CI."] },
  { id: "questions", quarter: 3, title: "What reporters ask", steps: 3, seconds: 35, Comp: Questions,
    notes: ["What reporters ask, with the ten LDA topics from the method slide. Grey: superstar − role gap in each topic's share of the questions.", "Raw: superstars get more about tonight's performance, shooting, the fourth quarter; role players about the Finals stage and legacy.", "Click: but role players talk mostly at the Finals (62% vs 47%) and less after games (32% vs 58%). Gold = same round and game day: most gaps shrink toward zero.", "Click: 3 of 10 still differ (shooting; season run; championship and legacy); 10 tests, no correction. So the questions differ mostly by situation too, and topic shares are controls in the model.", "Try: hover or click a topic for its words and both gaps."] },
  { id: "words", quarter: 3, title: "What they talk about", steps: 3, seconds: 35, Comp: Words,
    notes: ["Fightin' Words (Monroe 2008): log-odds with an informative Dirichlet prior (0.1 × all player answers), z-scores; names, teams, cities removed; words with ≥ 20 uses and ≥ 10 players. Why: raw differences favour common words.", "Click: superstars narrate the game; role players talk about being ready. Solid = holds per player (Mann–Whitney).", "Click: superstars use more of both “I” and “we”, so the share stays flat. Descriptive, no controls.", "Try: hover a word for its z score and whether it holds per player."] },
  { id: "classifiers", quarter: 3, title: "Can a model tell them apart?", steps: 3, seconds: 25, Comp: Classifiers,
    notes: ["Logistic regression, superstar vs role units; AUC on held-out players: 5-fold grouped by player, C tuned inside the training folds. Grouped because a player's style would leak into the test set.", "Click: pronoun rates alone ≈ chance.", "Click: all words 0.76, same without “I”/“we”: the difference is what they talk about. Part of it is length and session.", "Try: hover a row for the CI; click a ball to roll it again."] },
  { id: "robustness", quarter: 3, title: "Robustness", steps: 3, seconds: 40, Comp: Robustness,
    notes: ["14 planned checks, 13 include zero; grey row = counting words instead, same answer.", "Click: the exception: game days only, +6.2 (planned).", "Click: role players reach the podium after their own big games (+5.3 points): selection. A pattern to note, not a finding.", "Try: hover any check for its estimate and CI."] },
  { id: "final", quarter: 4, title: "Final score", steps: 4, seconds: 45, Comp: FinalScore,
    notes: ["So what's the answer? Read in context, no detectable difference in team focus by status; gaps beyond about 4.5 points ruled out, smaller ones not.", "Click: the situation goes with bigger shifts.", "Click: what they talk about differs.", "Click: takeaway, in one sentence (say it the same way on the fun fact)."] },
  { id: "limits", quarter: 4, title: "Limits and next steps", steps: 2, seconds: 45, Comp: Limits,
    notes: ["AI-made training labels; my blind check agrees 66% on “I” (κ 0.43), moderate; pronouns only; observational, playoffs; small gaps possible. Word counting needs no labels and gives the same answer.", "Click: next: human training labels from two coders, then retrain; coaches; beyond the playoffs. Why no lab effect: status vs reporters, not teammates (idea)."] },
  { id: "funfact", quarter: 4, title: "Fun fact", steps: 3, seconds: 20, Comp: FunFact,
    notes: ["Fun fact to finish: each dot is one player's pooled team-focused share (75 players with enough pronouns).", "Click: most team-focused by this measure (not “most selfless”): Steve Nash, 86%, then Kevin Love and Richard Hamilton.", "Click: least: Jalen Williams 37%, then Kawhi and Ayton. Both ends are superstars: players span about 50 points, the tier gap is half a point. Descriptive; with controls Nash is 4th, same bottom three.", "Try: hover a dot for the player."] },
  { id: "credits", quarter: 5, title: "Thank you", steps: 1, seconds: 5, Comp: Credits,
    notes: ["Thank you.", "Try: click the ball."] },
];

export const nextPos = (p: Pos): Pos =>
  p.s < SLIDES[p.i].steps - 1 ? { i: p.i, s: p.s + 1 } : p.i < SLIDES.length - 1 ? { i: p.i + 1, s: 0 } : p;

export const prevPos = (p: Pos): Pos =>
  p.s > 0 ? { i: p.i, s: p.s - 1 } : p.i > 0 ? { i: p.i - 1, s: SLIDES[p.i - 1].steps - 1 } : p;
