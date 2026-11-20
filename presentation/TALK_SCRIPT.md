# Talk script

## Slide 1 · Title

Hi, I'm Travis. My project asks one question: are superstars more self-focused than role players? I measure it with “I” and “we” in 4,058 NBA playoff press conferences, from 2004 to 2026.

[click]

## Slide 2 · Guess: superstar or role player?

Let's start with a guess. These are two real answers from the data: one from a superstar, one from a role player. Which is which? [one-second pause]

[click]

The first is all “we”: zero “I”, four “we”. The second is the reverse.

[click]

The “we” answer is LeBron James. The “I” answer is Shaun Livingston, a role player. That's the opposite of the stereotype. But two hand-picked answers prove nothing, so I collected all 37,017.

[click]

## Slide 3 · Two opposite predictions

The question underneath is whether status shows up in how people talk. The common belief says yes: people in the spotlight talk about themselves, so more “I” and less “we”.

[click]

Lab research says the reverse. In five studies, Kacewicz and colleagues found that the higher-status person in an interaction used fewer “I” words and more “we” words.

[click]

Why care? If pronouns track status, text alone could hint at who holds power. And NBA press conferences test a lab finding in public, unscripted, high-stakes speech, where status is public. My prediction follows the lab: superstars use relatively more “we”. I tested it in both directions.

[click]

## Slide 4 · From transcripts to data points

The data. I scraped 6,321 press-conference transcripts from ASAP Sports: every NBA playoff round on the site, from 2004 to 2026.

[click]

I removed the moderators' lines and the coaches, since coaches aren't on the players' status ladder. That leaves 37,017 player answers.

[click]

99.5% of them match official NBA records through nba_api: results, points, minutes and starts. The All-Star lists come from Wikipedia.

[click]

The unit is one player in one press conference: 4,425 units from 377 players, 4,415 of them with pronouns. Why this data? Status is public, the speech is unscripted, and the same players face reporters year after year.

[click]

## Slide 5 · Three tiers of status

Status has three tiers, set each season. A superstar is an All-Star that season, injured picks included. Of the rest, a starter started at least half of their regular-season games, and a role player started fewer.

[click]

That gives 957 role-player units, 1,563 starter units and 1,905 superstar units.

[click]

The tier follows the season, so 86 players change tier, like Draymond Green. And the tiers differ in other ways: superstars talk more, and 58% of their press conferences come after a game, against 32% for role players. That's why the model needs controls.

[click]

## Slide 6 · Counting words misses the meaning

The obvious measure is to count “I” and “we”. Here's Kobe Bryant in 2008: “It is not me at the forefront. That's just not how we roll.”

[click]

Two “I” words, two “we” words: a we-share of 0.50. It calls this answer half self-focused, and it's all about the team.

[click]

There are three problems. “I think” and “I mean” are conversation, not self-focus, and that's 38% of all “I”. “It's not about me” gives the credit away, but still counts. And about one “we” in ten isn't the team. So I read each word in its sentence.

[click]

## Slide 7 · BERT: a contextual embedding for every “I”

For that I used BERT, bert-base-uncased, frozen. For each “I” and “we”, I take the mean of the last four layers, 768 dimensions, with the full answer as context.

[click]

The same token gets a different vector in each sentence. Butler's “I was 0-for-2” is about himself, Nance's “I mean” is conversation, and Kawhi's “It's really not about me” gives the credit away.

[click]

Each one's nearest neighbour by cosine, among other players' “I”, has the same use: Kawhi's is closest to LeBron's “It's not about me”, at 0.84. So a linear classifier on these vectors should be able to separate the uses.

[click]

## Slide 8 · 720 labelled uses train a classifier

A classifier needs labels. I sampled 720 uses, 300 random and 60 targeted per word, and a blind AI coder labelled them: “I” as self, team or conversation; “we” as team or not.

[click]

An L2 logistic regression on the vectors, with five-fold cross-validation grouped by player, gets 90% accuracy on held-out players, against a 60% majority baseline. Then it labels all 111,278 “I”.

[click]

Are the labels right? A second blind AI coder agrees 100% on random uses and 82% on targeted ones. My own blind check of 100 random uses: 92% on “we”, but only 66% on “I”, kappa 0.43, mostly on framing verbs like “I think”. The bar was set beforehand: “I” passes; “we” doesn't beat its majority baseline, so it isn't used.

[click]

## Slide 9 · Read in context, 38% of “I” is just conversation

Counting calls all four of these self-focus.

[click]

BERT reads them as self, conversation and team. But it still reads Kobe's “me” as self, so that's a miss. Over all 111,278 “I” words, 38% are conversation, and the mix is about the same in every tier.

[click]

That gives the main measure, the team-focused share: team “I” plus “we”, divided by self “I” plus team “I” plus “we”. Conversation “I” is left out. It finds about half of the credit-giving “I”, and I made it the main measure after a first analysis with counting. Both measures give the same answer.

[click]

## Slide 10 · Does “we” mean the team?

Does “we” mean the team? In 30 random uses per tier, one per player, about 9 in 10 do, in every tier.

[click]

They were coded twice, once blind to the tier, with 94% agreement, kappa 0.76. Both coders were AI models. And since BERT couldn't beat the baseline for “we”, every “we” counts as team.

[click]

## Slide 11 · Comparing like with like

Now the comparison: does tier go with the team-focused share, once we compare like with like?

[click]

Six things go with pronoun use and differ by tier: winning or losing, points and minutes, the round, the reporter's wording, measured as “you” in the question, the question topics, and game day.

[click]

So: a binomial GLM with a logit link, team out of self plus team pronouns per unit, because it's a count out of a total. Standard errors are clustered by player, since players appear many times, and player fixed effects compare the same player across seasons. The topics come from LDA: next slide.

[click]

## Slide 12 · LDA turns each unit's questions into ten topic shares

One document is every question to one player in one press conference: here, LeBron's from slide 2. After removing stop words, filler and 946 name words, I keep one- and two-word terms in at least 10 documents and at most half: 3,263 terms, as raw counts.

[click]

LDA with K = 10 gives each document a topic mix, theta: this one is two-thirds championship and legacy. The ten shares are controls in the GLM.

[click]

K was chosen from 5 to 20 by NPMI coherence and seed stability. K = 5 scores higher but merges themes; K = 10 is the best from 8 to 15, and every topic can be named.

[click]

## Slide 13 · The team-focused share is about the same in every tier

So, does status show up? With all controls, the team-focused share is 65.0% for role players, 65.6% for starters and 64.5% for superstars.

[click]

Each dot is a tier's adjusted share with its 95% interval: no controls, all controls, and within the same player. The tiers overlap at every stage.

[click]

Superstar minus role player is minus 0.5 points, with a 95% confidence interval from minus 4.5 to plus 3.6. Within the same player, it's plus 0.9. [two-second pause]

[click]

So the data rule out a gap bigger than about four and a half points either way, about a fifth of a standard deviation, but not a smaller one. My prediction isn't supported, and neither is the common belief.

[click]

## Slide 14 · Winning and losing go with bigger shifts than status

The same model shows what goes with bigger shifts. These are average marginal effects. After a win, players are 9.1 points less team-focused than after a loss. More “you” in the question goes with less team focus, and the conference finals with more.

[click]

Status is the smallest shift on the chart.

[click]

And that's the opposite of fans. In Cialdini's study, fans used “we” more after wins. Players here are more team-focused after losses: 73% against 60%. They're different measures, so treat it as a contrast.

[click]

## Slide 15 · Question topics differ by tier, mostly through timing

LDA also shows what reporters ask. Raw, superstars get more about tonight's performance and shooting, and role players more about the Finals stage and legacy. But role players speak mostly at the Finals, and less often after games.

[click]

With round and game day held equal, the gold dots, most gaps shrink toward zero.

[click]

Three of ten still differ, from ten tests with no correction. So the questions also differ mostly by situation.

[click]

## Slide 16 · They differ in what they talk about

So what does differ? Fightin' Words: log-odds with an informative Dirichlet prior, so neither rare nor very common words dominate, with names and teams removed. Superstars say “tonight”, “quarter”, “missed”, “aggressive”; role players say “ready” and “here”. The solid ones hold per player.

[click]

Superstars narrate the game; role players talk about being ready.

[click]

And superstars use more of both “I” and “we” per thousand words, so the share stays flat. This is descriptive, with no controls.

[click]

## Slide 17 · Words predict the tier; “I” and “we” add almost nothing

Can a model tell the tiers apart? Logistic regression on superstar versus role-player units, with AUC on held-out players.

[click]

“I” and “we” rates alone: 0.54, about chance.

[click]

All words: 0.76, and the same without “I” and “we”. Part of that is length and session: answer length alone reaches 0.70. So the words differ; the pronouns add almost nothing.

[click]

## Slide 18 · 14 checks: 13 include zero

Does it hold up? Fourteen checks: All-NBA instead of All-Star, without LeBron, Finals only, five topics, season fixed effects and more. Thirteen include zero, and counting words instead of BERT gives minus 0.4, the same answer.

[click]

The exception is game days only: plus 6.2, a check I planned.

[click]

But on game days, role players score 5.3 points above their own playoff average, and superstars only 0.9. Role players reach the podium after their own big games, so part of this is likely selection. It's a pattern to note, not a finding.

[click]

## Slide 19 · Final score

So, the final score. Status and team focus: minus 0.5 points, and gaps beyond about 4.5 are ruled out.

[click]

The situation goes with bigger shifts: minus 9.1 after a win, and the wording and the round go with shifts too.

[click]

And the words differ: superstars narrate the game, role players talk about being ready.

[click]

[look at the camera] So the takeaway: read in context, superstars and role players are about equally team-focused when they say “I” and “we”. Winning, losing and the questions asked go with bigger differences.

[click]

## Slide 20 · What this can't say, and what's next

Four limits. One: the training labels are AI-made, and my own check agrees only 66% on “I”. Word counting needs no labels and gives the same answer. Two: pronouns are one view of self-focus; teammate credit does differ between players, though not within a player. Three: it's observational and playoffs only, so consistent with, not proof. Four: gaps under 4.5 points are still possible.

[click]

Next: human training labels from two coders, then retrain; coaches; and beyond the playoffs. One idea to test for the missing lab effect: at the podium, status is set against reporters, not teammates.

[click]

## Slide 21 · Most and least team-focused at the podium

To finish, a fun fact. Each dot is one player.

[click]

The most team-focused, by this measure: Steve Nash, at 86%.

[click]

The least: Jalen Williams, at 37%. Both are superstars. Players span 49 points; the tiers, half a point.

[click]

## Slide 22 · Thank you

Thank you for watching. [two-second pause, then stop]
