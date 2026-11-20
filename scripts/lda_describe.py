"""Step 7 LDA, described in more detail for the talk (18 Nov; descriptive, the model is not changed).

    cd scripts && python lda_describe.py        (about 3-8 minutes on 12 cores)

Refits the final K = 10 model exactly as lda_questions.py does (same matrix, seed 0, batch, 50 iterations) and checks
that the topic shares match data/unit_topics.csv. Then, for each topic:
  - top 30 words by probability p(word | topic) (what lda_topics.txt lists, longer)
  - top 15 "exclusive" words: highest lift p(word | topic) / p(word) among words with >= 200 uses, i.e. the words that
    belong to this topic more than to the others (the probability list repeats common words such as "tonight")
  - share of all question words, and mean share per tier
  - the 3 units whose reporters' questions load most on the topic (first 220 characters of their questions)
Writes data/lda_topics_detail.txt.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import lda_questions as L

D = Path(__file__).resolve().parent.parent / "data"


def main():
    u = L.load()
    X, vec, _, _ = L.build_matrix(u)
    vocab = vec.get_feature_names_out()
    lda = L.fit(X, 10, L.SEEDS[0])
    theta = lda.transform(X)
    saved = u[["interview_id", "person_key"]].merge(pd.read_csv(D / "unit_topics.csv"), on=["interview_id", "person_key"],
                                                    how="left")
    cols = [f"topic_{i + 1}" for i in range(10)]
    diff = np.abs(saved[cols].values - theta).max()
    assert diff < 1e-6, f"refit does not reproduce unit_topics.csv (max diff {diff})"
    labels = pd.read_csv(D / "topic_labels.csv").set_index("topic")

    phi = lda.components_ / lda.components_.sum(1, keepdims=True)             # p(word | topic)
    counts = np.asarray(X.sum(0)).ravel()
    pw = counts / counts.sum()                                                 # p(word)
    lift = phi / pw
    lift[:, counts < 200] = 0
    doc_len = np.asarray(X.sum(1)).ravel()
    word_share = (theta * doc_len[:, None]).sum(0) / doc_len.sum()

    lines = [f"LDA on the reporters' questions, K = 10 (refit check: max difference from unit_topics.csv {diff:.1e})",
             f"Documents: {X.shape[0]:,} units (all questions to one player in one press conference); "
             f"vocabulary {X.shape[1]:,} terms (single words and two-word phrases).",
             "Exclusive words = highest lift p(word | topic) / p(word), words with at least 200 uses.", ""]
    for k, c in enumerate(cols):
        top = [vocab[i] for i in phi[k].argsort()[::-1][:30]]
        exc = [vocab[i] for i in lift[k].argsort()[::-1][:15]]
        mean = pd.Series(theta[:, k]).groupby(u.tier).mean()
        lines += [f"== {c}: {labels.label[c]}  (NPMI {labels.npmi[c]:+.2f}, stability {labels.stability[c]:.2f}; "
                  f"{100 * word_share[k]:.1f}% of question words; mean share role {mean.get('role', 0):.3f}, "
                  f"starter {mean.get('starter', 0):.3f}, superstar {mean.get('superstar', 0):.3f})",
                  "top 30 by probability: " + ", ".join(top),
                  "most exclusive: " + ", ".join(exc),
                  "questions that load most on it:"]
        for j in theta[:, k].argsort()[::-1][:3]:
            q = " ".join(str(u.questions[j]).split())[:220]
            lines.append(f"  [{theta[j, k]:.2f}] {u.person[j]}, {u.season[j]}: {q} ...")
        lines.append("")
    (D / "lda_topics_detail.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
