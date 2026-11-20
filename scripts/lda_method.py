"""How the Step 7 LDA works, shown on one document (18 Nov, Step 22; descriptive, the model is not changed).

    cd scripts && python lda_method.py        (about 3-8 minutes on 12 cores: refits K = 10)

Refits the final K = 10 model exactly as lda_questions.py does (same matrix, seed 0, batch variational Bayes,
50 iterations, alpha = eta = 1/K) and checks that the topic shares match data/unit_topics.csv. Then:
  - corpus numbers: documents, terms (single words and two-word phrases), tokens kept, words removed
  - the example document: LeBron James, 2016 conference finals Game 6 (the unit of the slide 2 quote):
      * four of its questions, word by word: kept as a vocabulary term or removed (and why)
      * for each kept word, its most likely topic in this document, argmax_k theta_dk * phi_kw
      * its count vector (top terms) and its topic shares theta_d
  - the K sweep (data/lda_sweep.csv) and the alpha check (data/lda_topics.txt)
Writes data/lda_method.json and data/lda_method.txt.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

import lda_questions as L

D = Path(__file__).resolve().parent.parent / "data"
EXAMPLE = (119675, "lebron james")          # 27 May 2016, conference finals Game 6 win; slide 2 quote
EXCERPT = [                                  # four of its ten questions, verbatim
    "LeBron, as you know, you've fought against this idea all year that the Cavs were preordained to be in The Finals, "
    "that you were supposed to be here.",
    "LeBron, this is the second straight year you guys made The Finals.",
    "LeBron, city of Cleveland hasn't won a championship in over 50 years. Being from Akron, how does it feel to kind "
    "of have a shot to beat the drought?",
    "LeBron, during the regular season you said your team is okay, it's not great.",
]


def reason(w, vocab, names, stop_all, too_common):
    """Why a word of the raw question is or is not a vocabulary term (checks the word before and after plural folding,
    because the stop list holds both forms)."""
    w2 = w.replace("’", "'")
    if re.fullmatch(r"[A-Za-z]+'[A-Za-z]+", w2) and not w2.lower().endswith("'s"):
        return "contraction"
    c = L.clean(w).strip()
    if not re.fullmatch(r"[a-z]{3,}", c):
        return "under 3 letters"
    if c in vocab:
        return "kept"
    forms = {re.sub(r"'s$", "", w2.lower()), c}
    for cat, words in [("name word", names), ("stop word", ENGLISH_STOP_WORDS), ("spoken filler", L.FILLER),
                       ("generic word", L.GENERIC), ("stenographer note", L.TRANSCRIPT)]:
        if forms & set(words):
            return cat
    if c in stop_all:
        return "stop word"
    return "max_df" if c in too_common else "min_df"


def main():
    u = L.load()
    X, vec, names, too_common = L.build_matrix(u)
    vocab = vec.get_feature_names_out()
    vset = {t: i for i, t in enumerate(vocab)}
    lda = L.fit(X, 10, L.SEEDS[0])
    theta = lda.transform(X)
    saved = u[["interview_id", "person_key"]].merge(pd.read_csv(D / "unit_topics.csv"), on=["interview_id", "person_key"],
                                                    how="left")
    cols = [f"topic_{i + 1}" for i in range(10)]
    diff = float(np.abs(saved[cols].values - theta).max())
    assert diff < 1e-6, f"refit does not reproduce unit_topics.csv (max diff {diff})"
    phi = lda.components_ / lda.components_.sum(1, keepdims=True)            # p(word | topic), 10 x V
    labels = pd.read_csv(D / "topic_labels.csv").set_index("topic").label

    # corpus numbers
    doc_len = np.asarray(X.sum(1)).ravel()
    corpus = {"docs": int(X.shape[0]), "terms": int(X.shape[1]), "bigrams": int(sum(" " in t for t in vocab)),
              "tokens_kept": int(X.sum()), "question_words": int(u.q_words.sum()),
              "median_kept": float(np.median(doc_len)), "names_removed": len(names), "too_common": too_common,
              "nonzero_share": float(X.nnz / (X.shape[0] * X.shape[1]))}

    # the example document
    d = int(np.where((u.interview_id == EXAMPLE[0]) & (u.person_key == EXAMPLE[1]))[0][0])
    row = u.iloc[d]
    for q in EXCERPT:
        assert q in row.questions, q[:40]
    th = theta[d]
    stop_all = set(vec.get_stop_words())
    tokens = []
    for qi, q in enumerate(EXCERPT):
        for m in re.finditer(r"[A-Za-z’']+|[^A-Za-z’']+", q):
            w = m.group()
            if not re.match(r"[A-Za-z]", w):
                tokens.append({"t": w})
                continue
            why = reason(w, vset, set(names), stop_all, set(too_common))
            tok = {"t": w, "why": why}
            if why == "kept":
                term = L.clean(w).strip()
                resp = th * phi[:, vset[term]]
                resp = resp / resp.sum()
                k = int(resp.argmax())
                tok.update(term=term, topic=k + 1, p=round(float(resp[k]), 3))
            tokens.append(tok)
        if qi < len(EXCERPT) - 1:
            tokens.append({"t": " … ", "gap": True})
    xd = X[d].toarray().ravel()
    top_terms = [{"term": vocab[i], "n": int(xd[i]),
                  "topic": int((th * phi[:, i]).argmax()) + 1} for i in np.argsort(-xd)[:12] if xd[i] > 0]
    example = {"person": row.person, "season": int(row.season), "round": row["round"], "date": row.date,
               "game_day": int(row.game_day), "won": None if pd.isna(row.won) else int(row.won),
               "n_questions": int(row.n_answers), "q_words": int(row.q_words), "kept": int(xd.sum()),
               "distinct": int((xd > 0).sum()), "theta": [round(float(x), 4) for x in th],
               "tokens": tokens, "top_terms": top_terms}

    sweep = pd.read_csv(D / "lda_sweep.csv")
    alpha = [dict(alpha=float(a), npmi=float(n), diversity=float(v)) for a, n, v in
             re.findall(r"alpha = ([\d.]+): ([\d.]+), ([\d.]+)", (D / "lda_topics.txt").read_text(encoding="utf-8"))]
    out = {"corpus": corpus, "example": example, "check_max_diff": diff,
           "sweep": [{k: (int(v) if k == "K" else round(float(v), 4)) for k, v in r.items()} for r in sweep.to_dict("records")],
           "alpha": alpha,
           "topic_words": {f"topic_{k + 1}": [vocab[i] for i in phi[k].argsort()[::-1][:8]] for k in range(10)}}
    (D / "lda_method.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    kept = [t for t in tokens if t.get("why") == "kept"]
    removed = pd.Series([t["why"] for t in tokens if t.get("why") not in (None, "kept")]).value_counts()
    lines = ["How the LDA works, on one document (Step 22; descriptive; refit matches unit_topics.csv, "
             f"max diff {diff:.1e})", "",
             f"Corpus: {corpus['docs']:,} documents (one per unit: all reporters' questions to one player in one press "
             f"conference); {corpus['terms']:,} terms ({corpus['bigrams']:,} two-word phrases); "
             f"{corpus['tokens_kept']:,} term tokens kept of {corpus['question_words']:,} question words; median "
             f"{corpus['median_kept']:.0f} per document; {corpus['names_removed']} name words removed; removed as too "
             f"common (max_df 0.5): {', '.join(too_common)}; matrix density {corpus['nonzero_share']:.2%}.", "",
             f"Example: {row.person}, {row.date} ({row['round']}, game day {row.game_day}, won {row.won}); "
             f"{row.n_answers} questions, {row.q_words} words -> {example['kept']} term tokens, {example['distinct']} "
             "distinct terms.",
             "theta_d: " + ", ".join(f"{labels[c]} {100 * x:.0f}%" for c, x in sorted(zip(cols, th), key=lambda z: -z[1])
                                     if x >= 0.01),
             "Top terms (count, most likely topic): " + ", ".join(f"{t['term']} {t['n']} (t{t['topic']})" for t in top_terms),
             f"Excerpt: {len(kept)} kept words; removed: " + ", ".join(f"{k} {v}" for k, v in removed.items()),
             "Kept words and topic (argmax theta_dk * phi_kw): " +
             ", ".join(f"{t['term']}->t{t['topic']} ({t['p']:.2f})" for t in kept), "",
             "K sweep (seed 0 coherence and diversity; stability over seeds 0-2):",
             sweep.round(3).to_string(index=False), "",
             "alpha check (K = 10): " + "; ".join(f"alpha {a['alpha']}: NPMI {a['npmi']}, diversity {a['diversity']}"
                                                  for a in alpha)]
    (D / "lda_method.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
