"""Step 19: numbers for the talk slide that explains what BERT is. Descriptive only; nothing in the analysis changes.

    cd scripts && python bert_explain.py        (about 2 minutes; needs the Step 17 vectors)

1. Fill in the blank: bert-base-uncased's own guesses for a hidden word in a real answer (how BERT was pre-trained).
2. Same word, different numbers: for the three example "I" words on the talk slides (the same lids as
   export_site_data.BERT_EXAMPLES), the 768 numbers (each standardised over all "I" words, as the classifier sees them),
   their similarity to each other, and the closest "I" words among all 111,278 (other players, one use per player).
   Similarity = cosine similarity of the standardised vectors (0 = unrelated, 1 = the same direction).

Writes data/bert_explain.json and data/bert_explain.txt.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from bert_pronouns import IDX, MODEL, TIERS, VEC, clean

DATA = Path(__file__).resolve().parent.parent / "data"
EXAMPLES = {"self": 299, "neither": 289, "team": 57}        # lid in data/bert_label/sample.csv (same as the talk slides)
BLANK = ("Larry Nance Jr.", 2018, "I mean, you hear it.", "mean")  # a real answer; the hidden word
N_NEIGHBOURS = 3


def fill_mask():
    import torch
    from transformers import AutoTokenizer, BertForMaskedLM
    tok = AutoTokenizer.from_pretrained(MODEL)
    m = BertForMaskedLM.from_pretrained(MODEL).eval()
    person, season, sentence, hidden = BLANK
    masked = sentence.replace(hidden, tok.mask_token, 1)
    enc = tok(masked, return_tensors="pt")
    with torch.no_grad():
        p = m(**enc).logits[0, (enc.input_ids[0] == tok.mask_token_id).nonzero()[0].item()].softmax(-1)
    top = p.topk(5)
    guesses = [{"word": tok.decode([int(i)]).strip(), "p": round(float(v), 4)} for v, i in zip(top.values, top.indices)]
    return {"person": person, "season": season, "sentence": sentence, "hidden": hidden,
            "masked": sentence.replace(hidden, "___", 1), "guesses": guesses}


def marked_sentence(text, s, e, max_len=110):
    """The sentence holding text[s:e], with the word written [[like this]]; long sentences are cut around the word."""
    a = max(text.rfind(p, 0, s) for p in (". ", "? ", "! "))
    a = 0 if a < 0 else a + 2
    m = re.search(r"[.?!](\s|$)", text[e:])
    b = e + m.end() if m else len(text)
    sent = (text[a:s] + "[[" + text[s:e] + "]]" + text[e:b]).strip()
    if len(sent) > max_len:                         # keep about max_len characters around the word, at word boundaries
        i = sent.index("[[")
        lo, hi = max(0, i - max_len // 2), min(len(sent), i + max_len // 2)
        lo = sent.rfind(" ", 0, lo) + 1 if lo > 0 else 0
        hi = sent.find(" ", hi) if sent.find(" ", hi) > 0 else len(sent)
        sent = ("… " if lo > 0 else "") + sent[lo:hi].strip() + (" …" if hi < len(sent) else "")
    return sent


def main():
    idx = pd.read_csv(IDX)
    idx["pid"] = np.arange(len(idx))
    pred = pd.read_csv(DATA / "bert_pronoun_pred.csv").set_index("pid").label
    s = pd.read_csv(DATA / "bert_label" / "sample.csv").set_index("lid")
    a = pd.read_csv(DATA / "answers_analysis.csv", usecols=["person", "season", "tier", "answer"])
    a = a[a.tier.isin(TIERS)].reset_index(drop=True)            # same row numbers as the embedding step
    text = a.answer.map(clean)

    m = (idx.family == "i").values
    sub = idx[m].reset_index(drop=True)
    x = np.asarray(np.load(VEC, mmap_mode="r")[m], dtype=np.float32)
    z = (x - x.mean(0)) / x.std(0)                              # standardised, as in the classifier (StandardScaler)
    zn = z / np.linalg.norm(z, axis=1, keepdims=True)
    pos = {p: k for k, p in enumerate(sub.pid)}

    out = {"n_i": int(m.sum()), "dims": int(x.shape[1]), "fill_mask": fill_mask(), "examples": {}, "similarity": {}}
    lines = ["Step 19: numbers for the slide that explains BERT (descriptive)", "",
             f"Fill in the blank ({out['fill_mask']['person']} {out['fill_mask']['season']}): \"{out['fill_mask']['masked']}\" -> " +
             ", ".join(f"{g['word']} {100 * g['p']:.0f}%" for g in out["fill_mask"]["guesses"]), ""]
    ex_rows = {}
    for kind, lid in EXAMPLES.items():
        pid = int(s.loc[lid].pid)
        k = pos[pid]
        ex_rows[kind] = k
        r = sub.loc[k]
        sims = zn @ zn[k]
        order = np.argsort(-sims)
        nb = []
        for j in order:
            if len(nb) == N_NEIGHBOURS:
                break
            rj = sub.loc[j]
            if a.person[rj.row] in {a.person[r.row]} | {n["person"] for n in nb}:   # other players, one use each
                continue
            nb.append({"person": a.person[rj.row], "season": int(a.season[rj.row]), "tier": a.tier[rj.row],
                       "similarity": round(float(sims[j]), 3), "label": pred[int(rj.pid)],
                       "context": marked_sentence(text[rj.row], int(rj.start), int(rj.end))})
        out["examples"][kind] = {"person": a.person[r.row], "season": int(a.season[r.row]), "word": r.word, "label": pred[pid],
                                 "context": marked_sentence(text[r.row], int(r.start), int(r.end)),
                                 "vector": [round(float(v), 2) for v in np.clip(z[k], -3, 3)],
                                 "median_similarity": round(float(np.median(sims)), 3), "neighbours": nb}
        lines.append(f"{kind}: {a.person[r.row]} {int(a.season[r.row])}: {out['examples'][kind]['context']}  (BERT label {pred[pid]}; "
                     f"median similarity to all \"I\" {np.median(sims):+.3f})")
        lines += [f"   {n['similarity']:.3f} {n['label']:<8} {n['person']} {n['season']}: {n['context']}" for n in nb]
    kinds = list(EXAMPLES)
    for i in range(len(kinds)):
        for j in range(i + 1, len(kinds)):
            v = round(float(zn[ex_rows[kinds[i]]] @ zn[ex_rows[kinds[j]]]), 3)
            out["similarity"][f"{kinds[i]}-{kinds[j]}"] = v
            lines.append(f"similarity {kinds[i]} vs {kinds[j]}: {v:+.3f}")
    (DATA / "bert_explain.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    (DATA / "bert_explain.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
