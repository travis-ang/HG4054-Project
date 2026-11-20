"""Exploratory check (18 Nov, after the freeze; descriptive only, not in any model).

How often does an "I" word sit inside a phrase that pushes credit away from the speaker,
such as "it's not about me", "it's not just me", "it is not me at the forefront"?
Pronoun counting scores these as self-focus although they mean the opposite.

Run: cd scripts && python deflection_check.py  ->  data/deflection_check.txt
"""
import re
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
TIERS = ["role", "starter", "superstar"]

# "it's not about me", "this isn't about me", "it is not me", "not just me", "not only me", "not me"
DEFLECT = re.compile(
    r"\b(?:it|this|that)(?:'s| is| was)? (?:not|n't|never|isn't|wasn't)\s*(?:about|on|all about|just about)\s+(me|myself)\b"
    r"|\b(?:it|this)(?:'s| is| was) not me\b"
    r"|\bnot (?:just |only )?me\b",
    re.I,
)


def main():
    a = pd.read_csv(DATA / "answers_analysis.csv", usecols=["person", "tier", "season", "answer", "i_count"])
    a = a[a.tier.isin(TIERS)].copy()
    a["answer"] = a.answer.astype(str)
    a["deflect"] = a.answer.map(lambda s: len(DEFLECT.findall(s)))
    g = a.groupby("tier").agg(answers=("answer", "size"), i_words=("i_count", "sum"), deflecting=("deflect", "sum")).loc[TIERS]
    g["per_1000_I"] = (1000 * g.deflecting / g.i_words).round(2)

    lines = [__doc__.strip(), "", "Pattern: " + DEFLECT.pattern, "", g.to_string(), "",
             f"All tiers: {int(g.deflecting.sum())} deflecting uses out of {int(g.i_words.sum())} 'I' words "
             f"({1000 * g.deflecting.sum() / g.i_words.sum():.2f} per 1,000).", "", "Examples (random, seed 1):"]
    for _, r in a[a.deflect > 0].sample(8, random_state=1).iterrows():
        m = DEFLECT.search(r.answer)
        s = max(0, m.start() - 70)
        lines.append(f"- {r.tier}, {r.person} {r.season}: ...{r.answer[s:m.end() + 40]}...")
    out = DATA / "deflection_check.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[3:]))


if __name__ == "__main__":
    main()
