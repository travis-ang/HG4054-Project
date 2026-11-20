"""Human check of the BERT training labels (19 Nov, Step 23; a check only: the classifier and every result stay as they are).

    cd scripts && python human_check.py        (about 1 minute)

Travis labelled the 100 random uses of the 220-item check set (47 "I", 53 "we") blind, in
data/bert_label/label_tool_random100.html (no names or tiers; same rules as the AI coders), first pass only:
data/bert_label/labels_travis_check.csv. The 120 targeted uses were not labelled by a human.

Compares his labels with
  - the training labels (blind AI coder, labels_agent.csv), Claude (labels_claude.csv), the second AI coder
    (labels_agent2_check.csv): % agreement and Cohen's kappa per word, with confusion tables;
  - the classifier's held-out predictions for the same "I" uses: rebuilt exactly as bert_pronouns.py train() made
    them (C = 1, StratifiedGroupKFold(5, shuffle, random_state 0) by player) and checked against the reported
    macro-F1 0.776 / accuracy 0.897; nothing is saved over the Step 17 files;
  - the rule "every we = team" for "we".
Writes data/human_check.json and data/human_check.txt.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

D = Path(__file__).resolve().parent.parent / "data"
L = D / "bert_label"
CODERS = {"training labels (AI coder)": "labels_agent.csv", "Claude": "labels_claude.csv", "second AI coder": "labels_agent2_check.csv"}


def heldout_i(s):
    """Out-of-fold classifier labels for the 360 labelled "I" uses, as in bert_pronouns.train()."""
    d = s[(s.family == "i") & s.y.notna()].reset_index(drop=True)
    X = np.asarray(np.load(D / "bert_pronoun_vectors.npy", mmap_mode="r")[d.pid.values], dtype=np.float32)
    oof = np.empty(len(d), dtype=object)
    for tr, te in StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=0).split(X, d.y.values, d.person.values):
        m = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, class_weight="balanced", max_iter=3000))
        oof[te] = m.fit(X[tr], d.y.values[tr]).predict(X[te])
    f1, acc = f1_score(d.y, oof, average="macro"), accuracy_score(d.y[d.source == "random"], oof[d.source == "random"])
    assert round(f1, 3) == 0.776 and round(acc, 3) == 0.897, (f1, acc)
    return d.assign(clf=oof), f1, acc


def compare(t, o, fam):
    m = t[t.family == fam].merge(o, on="lid", suffixes=("_t", "_o"))
    agree = int((m.label_t == m.label_o).sum())
    return m, {"n": len(m), "agree": agree, "pct": round(100 * agree / len(m)), "kappa": round(float(cohen_kappa_score(m.label_t, m.label_o)), 2)}


def main():
    s = pd.read_csv(L / "sample.csv").merge(pd.read_csv(L / "labels_agent.csv")[["lid", "label"]].rename(columns={"label": "y"}),
                                            on="lid", how="left")
    t = pd.read_csv(L / "labels_travis_check.csv")
    src = s.set_index("lid").loc[t.lid, "source"]
    assert len(t) == 100 and (src == "random").all() and t.lid.is_unique
    out = {"n": len(t), "n_i": int((t.family == "i").sum()), "n_we": int((t.family == "we").sum()), "vs": {}}
    lines = ["Human check of the BERT training labels (Step 23): Travis, blind, first pass, 100 random uses", ""]
    for name, f in CODERS.items():
        o = pd.read_csv(L / f)[["lid", "label"]]
        out["vs"][name] = {}
        for fam in ["i", "we"]:
            m, r = compare(t, o, fam)
            out["vs"][name][fam] = r
            lines += [f"Travis vs {name}, \"{fam}\" ({r['n']}): {r['pct']}% ({r['agree']}/{r['n']}), kappa {r['kappa']:.2f}",
                      pd.crosstab(m.label_t.rename("Travis"), m.label_o.rename(name)).to_string(), ""]
    d, f1, acc = heldout_i(s)
    m, r = compare(t, d[["lid", "clf"]].rename(columns={"clf": "label"}), "i")
    out["vs"]["classifier (held-out players)"] = {"i": r}
    both = m[(m.label_t != "neither") & (m.label_o != "neither")]
    out["self_team_both"] = {"n": len(both), "agree": int((both.label_t == both.label_o).sum())}
    lines += [f"Classifier rebuilt as in Step 17 (macro-F1 {f1:.3f}, random-part accuracy {acc:.3f}: matches).",
              f"Travis vs classifier (held-out players), \"I\" ({r['n']}): {r['pct']}% ({r['agree']}/{r['n']}), kappa {r['kappa']:.2f}",
              pd.crosstab(m.label_t.rename("Travis"), m.label_o.rename("classifier")).to_string(),
              f"Uses both call self or team: {out['self_team_both']['agree']}/{out['self_team_both']['n']} agree.", ""]
    ti, tw = t[t.family == "i"].label.value_counts(), t[t.family == "we"].label.value_counts()
    ai = s.set_index("lid").loc[t[t.family == "i"].lid, "y"].value_counts()
    out["shares"] = {"travis_i": ti.to_dict(), "training_i": ai.to_dict(), "classifier_i": m.label_o.value_counts().to_dict(),
                     "travis_we_team": int(tw.get("team", 0))}
    lines += [f"\"I\" labels on these 47: Travis {ti.to_dict()}; training labels {ai.to_dict()}; classifier {m.label_o.value_counts().to_dict()}",
              f"\"we\": Travis team {tw.get('team', 0)} of {tw.sum()} ({100 * tw.get('team', 0) / tw.sum():.0f}%); the rule every \"we\" = team "
              f"agrees on the same share", ""]
    a = pd.read_csv(L / "labels_agent.csv").set_index("lid").label
    dis = t[(t.family == "i")].assign(training=lambda x: a.loc[x.lid].values)
    dis = dis[dis.label != dis.training]
    out["i_disagreements"] = [{"lid": int(x.lid), "travis": x.label, "training": x.training} for _, x in dis.iterrows()]
    lines.append("\"I\" disagreements with the training labels (lid: Travis / training): " +
                 ", ".join(f"{x.lid}: {x.label} / {x.training}" for _, x in dis.iterrows()))
    (D / "human_check.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    (D / "human_check.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
