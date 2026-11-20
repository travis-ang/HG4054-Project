"""Step 16: export every number the presentation website shows -> presentation/src/data/results.json.

    cd scripts && python export_site_data.py        (about 20 seconds)

Reads only saved results (Steps 6-15); nothing is refitted. Quotes are real answers from
answers_analysis.csv, with "I" and "we" words marked using the same word lists as the models.
"""
import json
import re
from pathlib import Path

import pandas as pd

import fightin_words as F
from slide_figures import load_units, TIERS

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "presentation" / "src" / "data" / "results.json"
TOKEN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|[^A-Za-z]+")
I_SET, WE_SET = set(F.I_WORDS), set(F.WE_WORDS)


def r(x, k=6):                       # keep 6 decimals so the site's own rounding matches the result files
    return None if pd.isna(x) else round(float(x), k)


def tokens(text):
    """Split a quote into runs, marking the "I" and "we" words."""
    out = []
    for t in TOKEN.findall(text):
        w = t.lower().replace("’", "'")
        out.append({"t": t, "k": "i" if w in I_SET else "we" if w in WE_SET else ""})
    return out


def context_tokens(text):
    """Tokens of a coded "we" context; the coded word (written [[like this]]) gets k = "target"."""
    out, nxt = [], False
    for tk in tokens(text):
        t = tk["t"]
        if "[[" in t:
            t, nxt = t.replace("[[", ""), True
        t = t.replace("]]", "")
        if nxt and tk["k"]:
            tk, nxt = {**tk, "k": "target"}, False
        if t:
            out.append({**tk, "t": t})
    assert sum(x["k"] == "target" for x in out) == 1, text
    return out


def quote(a, person, season, starts):
    row = a[(a.person == person) & (a.season == season) & a.answer.str.startswith(starts)]
    assert len(row) == 1, (person, season, starts, len(row))
    q = row.iloc[0]
    return {"person": person, "player_id": int(q.player_id), "tier": q.tier, "season": int(q.season),
            "round": q["round"], "game_day": int(q.game_day), "i": int(q.i_count), "we": int(q.we_count),
            "tokens": tokens(q.answer)}


BERT_EXAMPLES = {"self": 299, "neither": 289, "team": 57}   # lid in data/bert_label/sample.csv; every coder and the classifier agree


def sentence_of(context):
    """The sentence of a labelled context that holds the [[target]]."""
    i = context.index("[[")
    a = max(context.rfind(p, 0, i) for p in (". ", "? ", "! "))
    a = 0 if a < 0 else a + 2
    ends = [m.end() for m in re.finditer(r"[.?!](\s|$)", context) if m.end() > i]
    return context[a:ends[0] if ends else len(context)].strip()


def bert():
    """Step 17 (exploratory): "I" read in context with BERT. Reads the saved outputs of bert_pronouns.py; nothing is refitted."""
    pr = pd.read_csv(DATA / "bert_pronoun_pred.csv")
    idx = pd.read_csv(DATA / "bert_pronoun_index.csv")
    idx["pid"] = range(len(idx))
    lab = pr.set_index("pid").label
    be = pd.read_csv(DATA / "bert_effects.csv")
    bs = be[(be.tier == "superstar") & (be.spec == "4 + question topics")].set_index("analysis")
    eff = lambda k: {"diff": r(bs.loc[k, "diff"]), "lo": r(bs.loc[k, "diff_lo"]), "hi": r(bs.loc[k, "diff_hi"]), "p": r(bs.loc[k, "p"]),
                     "n_units": int(bs.loc[k, "n_units"]), "n_players": int(bs.loc[k, "n_players"])}
    mix = pd.read_csv(DATA / "bert_i_mix.csv", index_col=0)
    i_all = pr[pr.family == "i"].label.value_counts(normalize=True)

    txt = (DATA / "bert_classifier.txt").read_text(encoding="utf-8")
    c = re.search(r"chosen C = [\d.]+; held-out players: macro-F1 ([\d.]+) \(all labelled\), random part: accuracy ([\d.]+) "
                  r"vs majority class ([\d.]+).*?PASSES.*?\n.*?\n.*?\n.*?\n.*?\nteam\s+(\d+)\s+(\d+)\s+(\d+)", txt, re.S)
    assert c, "\"I\" classifier line not found"
    team_row = [int(v) for v in c.groups()[3:]]

    s = pd.read_csv(DATA / "bert_label" / "sample.csv")
    for f, col in [("labels_agent.csv", "a1"), ("labels_agent2_check.csv", "a2"), ("labels_claude.csv", "cl")]:
        s = s.merge(pd.read_csv(DATA / "bert_label" / f)[["lid", "label"]].rename(columns={"label": col}), on="lid", how="left")
    s = s.set_index("lid")
    ex = {}
    for kind, lid in BERT_EXAMPLES.items():
        x = s.loc[lid]
        assert x.family == "i" and x.a1 == x.a2 == lab[x.pid] == kind and (pd.isna(x.cl) or x.cl == kind), (kind, lid)
        ex[kind] = {"person": x.person, "tier": x.tier, "season": int(idx.season[x.pid]), "tokens": context_tokens(sentence_of(x.context))}

    # Kobe's "It is not me at the forefront" (the slide 6 answer): how the classifier reads that "me"
    a = pd.read_csv(DATA / "answers_analysis.csv", usecols=["person", "season", "tier", "answer"])
    a = a[a.tier.isin(TIERS)].reset_index(drop=True)
    row = a.index[(a.person == "Kobe Bryant") & (a.season == 2008) & a.answer.str.startswith("I honestly don't believe in sole leadership.")]
    assert len(row) == 1
    k = idx[(idx.row == row[0]) & (idx.word == "me")]
    assert len(k) == 1
    return {
        "n_i": int((pr.family == "i").sum()), "n_we": int((pr.family == "we").sum()), "n_labelled": len(s),
        "mix": {t: {kind: r(mix.loc[f"i:{kind}", t] / 100, 4) for kind in ["self", "neither", "team"]} for t in TIERS},
        "mix_all": {kind: r(i_all[kind], 4) for kind in ["self", "neither", "team"]},
        "classifier": {"macro_f1": float(c.group(1)), "accuracy": float(c.group(2)), "baseline": float(c.group(3)),
                       "team_found": team_row[2], "team_total": sum(team_row)},
        "we_classifier_used": bool(pr[pr.family == "we"].passes.all()),
        "original": eff("A original we-share, same units"), "corrected": eff("A corrected we-share"),
        "same_player": eff("B corrected we-share, same player (FE)"),
        "examples": ex, "kobe_me": lab[k.pid.iloc[0]],
    }


def bert_main():
    """Step 18: the BERT measure as the main measure (share of team-focused pronouns). Reads data/bert_effects.csv
    (Step 17 models A and B), data/bert_slide_effects.csv, data/bert_robustness.csv and data/bert_main_results.txt."""
    e = pd.read_csv(DATA / "bert_effects.csv")
    main_r = {}
    for key, an, spec in [("no_controls", "A corrected we-share", "1 Tier only"), ("all_controls", "A corrected we-share", "4 + question topics"),
                          ("same_player", "B corrected we-share, same player (FE)", "4 + question topics")]:
        g = e[(e.analysis == an) & (e.spec == spec)].set_index("tier")
        s = g.loc["superstar"]
        main_r[key] = {"tiers": {t: {"est": r(g.loc[t].estimate), "lo": r(g.loc[t].lo), "hi": r(g.loc[t].hi)} for t in TIERS},
                       "diff": r(s["diff"]), "lo": r(s.diff_lo), "hi": r(s.diff_hi), "p": r(s.p),
                       "odds_ratio": r(s.ratio), "n_units": int(s.n_units), "n_players": int(s.n_players)}
    se = pd.read_csv(DATA / "bert_slide_effects.csv")
    rb = pd.read_csv(DATA / "bert_robustness.csv")
    txt = (DATA / "bert_main_results.txt").read_text(encoding="utf-8")
    sel = {t: [float(v) for v in re.search(rf"^\s+{t}\s+([\d.]+)\s+([\d.]+)", txt, re.M).groups()] for t in TIERS}
    pooled = re.search(r"Pooled game-day share: after losses ([\d.]+), after wins ([\d.]+)", txt)
    sd = re.search(r"Unit share: mean ([\d.]+), SD ([\d.]+)", txt)
    units = re.search(r"Units with any self- or team-side pronoun: ([\d,]+) of", txt)
    assert main_r["all_controls"]["n_units"] == int(units.group(1).replace(",", ""))
    assert abs(r(se.loc[se.effect == "Superstar vs role player", "diff"].iloc[0]) - main_r["all_controls"]["diff"]) < 1e-6
    return {
        "main": main_r,
        "situation": [{"effect": x.effect, "diff": r(x["diff"]), "lo": r(x.lo), "hi": r(x.hi)} for _, x in se.iterrows()],
        "robustness": [{"check": x.check, "group": x.group, "diff": r(x["diff"]), "lo": r(x.diff_lo), "hi": r(x.diff_hi)}
                       for _, x in rb.iterrows()],
        "selection": {t: {"pts": sel[t][0], "min": sel[t][1]} for t in TIERS},
        "raw_gameday": {"lost": float(pooled.group(1)), "won": float(pooled.group(2))},
        "mean": float(sd.group(1)), "sd": float(sd.group(2)), "model_units": main_r["all_controls"]["n_units"],
    }


def bert_explain():
    """Step 19: the two slides that explain BERT and the labels. Reads data/bert_explain.json (bert_explain.py),
    data/bert_classifier.txt and data/bert_label/; nothing is refitted."""
    e = json.loads((DATA / "bert_explain.json").read_text(encoding="utf-8"))
    keep = ["person", "season", "tier", "similarity", "label"]
    ex = {k: {"person": x["person"], "season": x["season"], "word": x["word"], "label": x["label"], "vector": x["vector"],
              "tokens": context_tokens(x["context"]),
              "neighbours": [{**{c: n[c] for c in keep}, "tokens": context_tokens(n["context"])} for n in x["neighbours"]]}
          for k, x in e["examples"].items()}

    txt = (DATA / "bert_classifier.txt").read_text(encoding="utf-8")

    def agree(a, b, fam, part):
        m = re.search(rf"Agreement, {a} vs {b}, \"{fam}\", {part} \((\d+) uses\): (\d+)%, Cohen's kappa ([\d.]+)", txt)
        assert m, (a, b, fam, part)
        return {"n": int(m.group(1)), "pct": int(m.group(2)), "kappa": float(m.group(3))}

    def chosen(fam):
        m = re.search(rf"^\"{fam}\" C = .*?chosen C = ([\d.]+); held-out players: macro-F1 ([\d.]+) \(all labelled\), random part: "
                      rf"accuracy ([\d.]+) vs majority class ([\d.]+), macro-F1 ([\d.]+)\s+->\s+(PASSES|FAILS)", txt, re.S | re.M)
        assert m, fam
        sh = re.search(r"label shares in the random sample \(training labels\): (.*)", txt[m.end():]).group(1)
        return {"C": float(m.group(1)), "macro_f1": float(m.group(2)), "accuracy": float(m.group(3)), "baseline": float(m.group(4)),
                "passes": m.group(6) == "PASSES", "shares": {k: int(v) / 100 for k, v in re.findall(r"(\w+) (\d+)%", sh)}}

    conf = re.search(r"PASSES.*?\n.*?\n\s+neither\s+self\s+team\nneither\s+(\d+)\s+(\d+)\s+(\d+)\nself\s+(\d+)\s+(\d+)\s+(\d+)\n"
                     r"team\s+(\d+)\s+(\d+)\s+(\d+)", txt)
    assert conf, "\"I\" confusion matrix not found"
    cm = [int(v) for v in conf.groups()]
    cm = {k: {"right": cm[3 * j + j], "total": sum(cm[3 * j:3 * j + 3])} for j, k in enumerate(["neither", "self", "team"])}
    lab = DATA / "bert_label"
    s = pd.read_csv(lab / "sample.csv")
    comp = s.groupby(["family", "source"]).size()
    return {
        "n_vectors": int(len(pd.read_csv(DATA / "bert_pronoun_index.csv", usecols=["family"]))), "dims": e["dims"], "n_i": e["n_i"],
        "fill_mask": e["fill_mask"], "examples": ex, "similarity": e["similarity"],
        "sample": {"total": len(s), "random_per_word": int(comp[("i", "random")]), "targeted_per_word": int(comp[("i", "search")])},
        "n_second": len(pd.read_csv(lab / "labels_agent2_check.csv")), "n_claude": len(pd.read_csv(lab / "labels_claude.csv")),
        "agree": {"i_random": agree("AI agent", "AI agent 2", "I", "random"), "we_random": agree("AI agent", "AI agent 2", "we", "random"),
                  "i_targeted": agree("AI agent", "AI agent 2", "I", "targeted"), "we_targeted": agree("AI agent", "AI agent 2", "we", "targeted"),
                  "i_claude": agree("AI agent", "Claude", "I", "random"), "we_claude": agree("AI agent", "Claude", "we", "random")},
        "i": chosen("I"), "we": chosen("we"), "i_confusion": cm,
    }


# names on the slide (Step 21): clearer than the Step 7 labels where the top questions showed it (Doc, Step 20 tab)
TOPIC_NAME = {"First half: fouls and turnovers": "Halves, fouls and losses", "Pressure and mindset": "Matchups and challenges",
              "Individual performance": "Tonight's performance"}


def lda_tiers():
    """What reporters ask each tier (Step 21). Reads data/lda_tiers.csv/.txt (lda_tiers.py) and the exclusive words in
    data/lda_topics_detail.txt (lda_describe.py); descriptive."""
    t = pd.read_csv(DATA / "lda_tiers.csv")
    txt = (DATA / "lda_tiers.txt").read_text(encoding="utf-8")
    det = (DATA / "lda_topics_detail.txt").read_text(encoding="utf-8")
    fin = {k: float(v) for k, v in re.findall(r"(role|starter|superstar) ([\d.]+)", re.search(r"at the Finals: (.*?);", txt).group(1))}
    gd = {k: float(v) for k, v in re.findall(r"(role|starter|superstar) ([\d.]+)", re.search(r"on game days: (.*)", txt).group(1))}

    def words(topic):
        line = re.search(rf"== {topic}:.*?\nmost exclusive: (.*)", det, re.S).group(1).split("\n")[0]
        kept = []
        for w in line.split(", "):
            if not any(w in k.split() or k in w.split() for k in kept):
                kept.append(w)
        return kept[:6]
    topics = [{"topic": x.topic, "label": x.label, "name": TOPIC_NAME.get(x.label, x.label), "words": words(x.topic),
               "mean": {k: r(x[f"mean_{k}"]) for k in TIERS},
               "raw": {"d": r(x.raw), "lo": r(x.raw_lo), "hi": r(x.raw_hi)}, "adj": {"d": r(x.adj), "lo": r(x.adj_lo), "hi": r(x.adj_hi)},
               "holds": bool(x.holds)} for _, x in t.iterrows()]
    n_hold = int(re.search(r"(\d+) of 10 adjusted gaps exclude zero", txt).group(1))
    assert n_hold == sum(d["holds"] for d in topics)
    return {"finals": fin, "game_day": gd, "n_hold": n_hold, "topics": topics}


def human_check():
    """Step 23: Travis's blind check of the training labels, 100 random uses (first pass). Reads data/human_check.json
    (human_check.py); the classifier and every result are unchanged."""
    h = json.loads((DATA / "human_check.json").read_text(encoding="utf-8"))
    v = h["vs"]
    return {"n": h["n"], "n_i": h["n_i"], "n_we": h["n_we"], "i": v["training labels (AI coder)"]["i"],
            "we": v["training labels (AI coder)"]["we"], "i_classifier": v["classifier (held-out players)"]["i"],
            "we_team": h["shares"]["travis_we_team"], "i_splits": len(h["i_disagreements"])}


def lda_method():
    """Slide 12 (Step 22): how the LDA works, shown on one document. Reads data/lda_method.json (lda_method.py);
    descriptive, nothing refitted here."""
    m = json.loads((DATA / "lda_method.json").read_text(encoding="utf-8"))
    lab = pd.read_csv(DATA / "topic_labels.csv").set_index("topic").label
    name = {int(t.split("_")[1]): TOPIC_NAME.get(l, l) for t, l in lab.items()}
    ex = m["example"]
    theta = sorted([{"topic": k + 1, "name": name[k + 1], "share": r(x, 4)} for k, x in enumerate(ex["theta"])],
                   key=lambda d: -d["share"])
    # top terms for the slide; pairs of the same word ("year year") are skipped: two-word terms are formed after stop
    # words are removed, so such a pair is not a phrase (noted in the Step 22 Doc tab)
    terms = [t for t in ex["top_terms"] if len(set(t["term"].split())) == len(t["term"].split())][:6]
    keep = ["person", "season", "round", "date", "n_questions", "q_words", "kept", "distinct", "tokens"]
    return {"corpus": m["corpus"], "sweep": m["sweep"], "alpha": m["alpha"], "k": 10,
            "example": {**{k: ex[k] for k in keep}, "theta": theta, "terms": terms}, "topic_names": name}


def fun_fact():
    """Fun-fact slide (18 Nov): per-player team-focused share, players with >= 500 self + team pronouns and >= 10 units.
    Reads data/fun_fact.csv (fun_fact.py); descriptive."""
    f = pd.read_csv(DATA / "fun_fact.csv").sort_values("share", ascending=False).reset_index(drop=True)
    f["adj_rank"] = f.adjusted.rank(ascending=False, method="min").astype(int)
    from fun_fact import MIN_PRON as mp, MIN_UNITS as mu
    txt = (DATA / "fun_fact.txt").read_text(encoding="utf-8")
    assert f"== at least {mp} self+team pronouns and {mu} units: {len(f)} players" in txt
    assert ((f.pron >= mp) & (f.units >= mu)).all()
    return {
        "min_pron": mp, "min_units": mu, "n_players": len(f), "median": r(f.share.median()),
        "players": [{"person": x.person, "id": int(x.player_id), "share": r(x.share), "adjusted": r(x.adjusted), "adj_rank": int(x.adj_rank),
                     "tiers": x.tiers, "pron": int(x.pron), "units": int(x.units)} for _, x in f.iterrows()],
    }


def main():
    u = load_units()                                  # 4,425 units with questions (model sample)
    m = u[(u.i_count + u.we_count) > 0]
    out = {}

    out["sample"] = {
        "interviews_scraped": 6321, "player_answers": 37017, "matched_pct": 99.5,     # data_summary, match_report
        "units": len(u), "press_conferences": int(u.interview_id.nunique()), "players": int(u.person_key.nunique()),
        "model_units": len(m), "tier_changers": int((u.groupby("person_key").tier.nunique() > 1).sum()),
        "we_share_mean": r(m.we_share.mean()), "we_share_sd": r(m.we_share.std()),
        "median_words": {"superstar": 670, "role": 423},                                # Step 6
        "tiers": {t: {"units": int((u.tier == t).sum()), "players": int(u[u.tier == t].person_key.nunique()),
                      "game_day": int(((u.tier == t) & (u.game_day == 1)).sum()),
                      "other": int(((u.tier == t) & (u.game_day == 0)).sum())} for t in TIERS},
    }

    e = pd.read_csv(DATA / "model_effects.csv")
    main_r = {}
    for key, an, spec in [("no_controls", "A we-share", "1 Tier only"), ("all_controls", "A we-share", "4 + question topics"),
                          ("same_player", "B same player (FE)", "4 + question topics")]:
        g = e[(e.analysis == an) & (e.spec == spec)].set_index("tier")
        s = g.loc["superstar"]
        main_r[key] = {"tiers": {t: {"est": r(g.loc[t].estimate), "lo": r(g.loc[t].lo), "hi": r(g.loc[t].hi)} for t in TIERS},
                       "diff": r(s["diff"]), "lo": r(s.diff_lo), "hi": r(s.diff_hi), "p": r(s.p),
                       "odds_ratio": r(s.ratio), "n_units": int(s.n_units), "n_players": int(s.n_players)}
    out["main"] = main_r

    se = pd.read_csv(DATA / "slide_effects.csv")
    out["situation"] = [{"effect": x.effect, "diff": r(x["diff"]), "lo": r(x.lo), "hi": r(x.hi)} for _, x in se.iterrows()]
    out["raw_gameday_we_share"] = {"lost": 0.575, "won": 0.483}                     # model_results.txt

    s = pd.read_csv(DATA / "we_sample.csv")
    out["we_check"] = {"first": {t: int(((s.tier == t) & (s.referent == "team")).sum()) for t in TIERS},
                       "second": {"superstar": 26, "starter": 26, "role": 25},          # we_agreement.txt
                       "n": 30, "agreement_pct": 94, "kappa": 0.76}
    # the 90 coded uses, so each dot on the "we" slide can show its sentence (team uses first, as the dots are drawn)
    order = {"team": 0, "other_group": 1, "generic": 2}
    out["we_examples"] = {
        t: [{"person": x.person, "season": int(x.season), "word": x.word, "referent": x.referent,
             "note": None if pd.isna(x.note) else x.note, "tokens": context_tokens(x.context)}
            for _, x in s[s.tier == t].assign(o=lambda d: d.referent.map(order)).sort_values("o", kind="stable").iterrows()]
        for t in TIERS}
    assert all(len(v) == 30 for v in out["we_examples"].values())

    f = pd.read_csv(DATA / "fightin_words.csv")
    side = lambda d: [{"word": w.word, "z": r(w.z, 2), "holds": bool(w.mw_p < 0.05)} for _, w in d.iterrows()]
    out["words"] = {"superstar": side(f.sort_values("z", ascending=False).head(10)),
                    "role": side(f.sort_values("z").head(10)),
                    "families": {"i": {"superstar": 43.3, "role": 40.5, "z": 6.5},          # fightin_words.txt
                                 "we": {"superstar": 41.1, "role": 39.5, "z": 3.3}}}

    c = pd.read_csv(DATA / "classifier_results.csv").set_index("model")
    out["classifiers"] = {k: {"name": c.loc[k, "name"], "auc": r(c.loc[k, "auc_seed0"], 3), "lo": r(c.loc[k, "lo"], 3),
                              "hi": r(c.loc[k, "hi"], 3)} for k in ["E1", "E3", "B1", "B2", "E2", "E2b"]}

    lab = pd.read_csv(DATA / "topic_labels.csv").set_index("topic").label
    tcols = [f"topic_{k}" for k in range(1, 11)]
    tm = u.groupby("tier")[tcols].mean()
    out["topics"] = sorted([{"label": lab[tc], **{t: r(tm.loc[t, tc]) for t in TIERS}} for tc in tcols],
                           key=lambda d: d["superstar"] - d["role"], reverse=True)
    out["finals_share"] = {"role": 0.62, "superstar": 0.48}                          # Step 7

    rb = pd.read_csv(DATA / "robustness.csv")
    out["robustness"] = [{"check": x.check, "group": x.group, "diff": r(x["diff"]), "lo": r(x.diff_lo), "hi": r(x.diff_hi)}
                         for _, x in rb.iterrows()]
    txt = (DATA / "robustness.txt").read_text(encoding="utf-8")
    sel = {t: [float(v) for v in re.search(rf"^\s+{t}\s+([\d.]+)\s+([\d.]+)", txt, re.M).groups()] for t in TIERS}
    out["selection"] = {t: {"pts": sel[t][0], "min": sel[t][1]} for t in TIERS}

    a = pd.read_csv(DATA / "answers_analysis.csv",
                    usecols=["person", "player_id", "tier", "season", "round", "game_day", "answer", "i_count", "we_count"])
    out["quotes"] = {
        "hook_we": quote(a, "LeBron James", 2016, "We're still okay."),
        "hook_i": quote(a, "Shaun Livingston", 2016, "Just the adjustments."),
        "measure": quote(a, "Kobe Bryant", 2008, "I honestly don't believe in sole leadership."),
    }

    out["bert"] = bert()
    out["bert_main"] = bert_main()
    out["bert_explain"] = bert_explain()
    out["fun_fact"] = fun_fact()
    out["lda_tiers"] = lda_tiers()
    out["lda_method"] = lda_method()
    out["human_check"] = human_check()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT)
    for k, q in out["quotes"].items():
        print(k, q["person"], q["tier"], "I", q["i"], "we", q["we"],
              "marked", sum(t["k"] == "i" for t in q["tokens"]), sum(t["k"] == "we" for t in q["tokens"]))


if __name__ == "__main__":
    main()
