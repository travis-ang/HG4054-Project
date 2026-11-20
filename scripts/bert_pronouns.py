"""Step 17 (exploratory, after the freeze): context-aware "I" and "we" with BERT.

Every "I" and "we" word that the we-share counts gets a contextual embedding from bert-base-uncased
(Devlin et al., 2019): the mean of the last four hidden layers over the word's word pieces, with the
whole answer as context. These vectors are then clustered (k-means) and read, to sort each pronoun
by how it is used rather than by how it is spelled.

    cd scripts
    python bert_pronouns.py embed [N]        # vectors (N = only the first N answers, a quick test); about 2 hours on CPU
    python bert_pronouns.py sweep            # K = 4..12: stability, silhouette, sizes -> data/bert_sweep.txt
    python bert_pronouns.py sheets K_I K_WE  # final clusters + reading sheets (no names or tiers) -> data/bert_sheets/
    python bert_pronouns.py search           # nearest neighbours of seed deflections -> data/bert_sheets/deflection_search.md
    python bert_pronouns.py wecheck          # the 90 hand-coded "we" uses by cluster -> data/bert_wecheck.txt
    python bert_pronouns.py labelsheet       # 720 uses to label -> data/bert_label/label_tool.html (+ sample.csv key)
    python bert_pronouns.py train LABELS.csv # agreement, classifier (5-fold by player), a label for every use
    python bert_pronouns.py model [classifier|clusters] [RANK]   # corrected we-share, models A and B -> data/bert_results.txt

Outputs (embed): data/bert_pronoun_vectors.npy (float16, one row per pronoun) and
data/bert_pronoun_index.csv (which answer, which word, where in the answer).
"""
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
MODEL = "bert-base-uncased"
I_WORDS = {"i", "me", "my", "mine", "myself", "i'm", "i've", "i'll", "i'd"}     # same lists as the we-share
WE_WORDS = {"we", "us", "our", "ours", "ourselves", "we're", "we've", "we'll", "we'd"}
WORD = re.compile(r"[a-z']+")                                                     # same tokenizer as build_analysis_data.py
TIERS = ["role", "starter", "superstar"]
WIN, STRIDE, BATCH = 510, 256, 16
VEC, IDX = DATA / "bert_pronoun_vectors.npy", DATA / "bert_pronoun_index.csv"


def clean(s):
    return str(s).replace("’", "'")


def pronoun_spans(text):
    """(start, end, word, family) for every counted "I" / "we" word, found exactly as the we-share counts them."""
    out = []
    for m in WORD.finditer(text.lower()):
        w = m.group()
        if w in I_WORDS or w in WE_WORDS:
            out.append((m.start(), m.end(), w, "i" if w in I_WORDS else "we"))
    return out


def windows(n):
    """Start positions of overlapping windows of at most WIN word pieces covering n pieces."""
    if n <= WIN:
        return [0]
    starts = list(range(0, n - WIN, STRIDE)) + [n - WIN]
    return sorted(set(starts))


def embed(limit=None):
    import torch
    from transformers import AutoModel, AutoTokenizer

    torch.set_num_threads(max(1, torch.get_num_threads()))
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModel.from_pretrained(MODEL, output_hidden_states=True).eval()

    a = pd.read_csv(DATA / "answers_analysis.csv",
                    usecols=["interview_id", "turn", "person", "player_id", "tier", "season", "game_day", "answer", "i_count", "we_count"])
    a = a[a.tier.isin(TIERS)].reset_index(drop=True)
    if limit:
        a = a.head(limit)

    # 1. find the pronouns and the window each one is read in
    jobs, rows = [], []          # jobs: (answer row, window start, piece ids); rows: index entries
    for r, text in enumerate(a.answer.map(clean)):
        if r % 5000 == 0:
            print(f"  finding pronouns: {r:,}/{len(a):,} answers", flush=True)
        spans = pronoun_spans(text)
        if not spans:
            continue
        enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
        ids, offs = enc["input_ids"], enc["offset_mapping"]
        starts = windows(len(ids))
        wjob = {}
        for (s, e, w, fam) in spans:
            pieces = [k for k, (ps, pe) in enumerate(offs) if ps < e and pe > s]
            assert pieces, (r, w)
            mid = (pieces[0] + pieces[-1]) / 2
            ws = max(starts, key=lambda st: min(mid - st, st + WIN - mid))   # the window where the word sits most central
            if ws not in wjob:
                wjob[ws] = len(jobs)
                jobs.append((r, ws, ids[ws:ws + WIN]))
            rows.append({"row": r, "job": wjob[ws], "p0": pieces[0] - ws, "p1": pieces[-1] - ws + 1,
                         "start": s, "end": e, "word": w, "family": fam})
    idx = pd.DataFrame(rows)
    # the counts must match the we-share's own counts exactly
    got = idx.groupby(["row", "family"]).size().unstack(fill_value=0).reindex(range(len(a)), fill_value=0)
    assert (got.get("i", 0) == a.i_count).all() and (got.get("we", 0) == a.we_count).all(), "pronoun counts differ from i_count/we_count"
    print(f"{len(a):,} answers, {len(idx):,} pronouns ({(idx.family == 'i').sum():,} I, {(idx.family == 'we').sum():,} we), {len(jobs):,} windows")

    # 2. run BERT, longest windows together to waste little padding
    vec = np.zeros((len(idx), model.config.hidden_size), dtype=np.float16)
    by_job = idx.groupby("job").indices
    order = sorted(range(len(jobs)), key=lambda j: len(jobs[j][2]))
    cls, sep, pad = tok.cls_token_id, tok.sep_token_id, tok.pad_token_id
    t0 = time.time()
    with torch.inference_mode():
        for b in range(0, len(order), BATCH):
            js = order[b:b + BATCH]
            L = max(len(jobs[j][2]) for j in js) + 2
            ids = torch.full((len(js), L), pad, dtype=torch.long)
            att = torch.zeros((len(js), L), dtype=torch.long)
            for k, j in enumerate(js):
                p = [cls] + jobs[j][2] + [sep]
                ids[k, :len(p)] = torch.tensor(p)
                att[k, :len(p)] = 1
            hs = model(input_ids=ids, attention_mask=att).hidden_states
            h = torch.stack(hs[-4:]).mean(0)                      # mean of the last four layers
            for k, j in enumerate(js):
                for i in by_job[j]:
                    p0, p1 = idx.p0.iat[i] + 1, idx.p1.iat[i] + 1        # +1 for [CLS]
                    vec[i] = h[k, p0:p1].mean(0).numpy().astype(np.float16)
            if (b // BATCH) % 100 == 0:
                done = b + len(js)
                el = time.time() - t0
                print(f"  {done:,}/{len(jobs):,} windows  {el / 60:.1f} min  (about {el / done * (len(jobs) - done) / 60:.0f} min left)", flush=True)

    meta = a.loc[idx.row, ["interview_id", "turn", "person", "player_id", "tier", "season", "game_day"]].reset_index(drop=True)
    out = pd.concat([meta, idx[["row", "start", "end", "word", "family"]].reset_index(drop=True)], axis=1)
    suffix = "" if not limit else f"_test{limit}"
    np.save(VEC.with_name(VEC.stem + suffix + ".npy"), vec)
    out.to_csv(IDX.with_name(IDX.stem + suffix + ".csv"), index=False)
    print(f"done in {(time.time() - t0) / 60:.1f} min; wrote {len(out):,} vectors")


# ------------------------------------------------------------------ clustering
KS = [4, 6, 8, 10, 12]
SHEETS = DATA / "bert_sheets"
CLUSTERS = DATA / "bert_pronoun_clusters.csv"
FAMILY_NAME = {"i": "I", "we": "we"}


def answers():
    a = pd.read_csv(DATA / "answers_analysis.csv", usecols=["interview_id", "turn", "person", "tier", "answer"])
    a = a[a.tier.isin(TIERS)].reset_index(drop=True)          # same row numbers as the embedding step
    return a.answer.map(clean).tolist()


def load_vectors(family):
    """Vectors of one family with each word form's own mean removed (so groups form by context), unit length."""
    idx = pd.read_csv(IDX)
    idx["pid"] = np.arange(len(idx))
    m = (idx.family == family).values
    x = np.asarray(np.load(VEC, mmap_mode="r")[m], dtype=np.float32)
    sub = idx[m].reset_index(drop=True)
    for _, rows in sub.groupby("word").indices.items():
        x[rows] -= x[rows].mean(0)
    x /= np.linalg.norm(x, axis=1, keepdims=True) + 1e-8
    return sub, x


def reduce(x):
    from sklearn.decomposition import PCA
    return PCA(50, random_state=0).fit_transform(x)


def sweep():
    """K = 4..12 for "I" and "we": stability across 5 seeds (adjusted Rand index), silhouette, cluster sizes."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score, silhouette_score
    rows = []
    for fam in ["i", "we"]:
        sub, x = load_vectors(fam)
        z = reduce(x)
        samp = np.random.default_rng(0).choice(len(z), min(10000, len(z)), replace=False)
        for k in KS:
            labs = [KMeans(k, n_init=1, random_state=s).fit_predict(z) for s in range(5)]
            ari = np.mean([adjusted_rand_score(labs[i], labs[j]) for i in range(5) for j in range(i + 1, 5)])
            sil = silhouette_score(z[samp], labs[0][samp])
            size = np.bincount(labs[0], minlength=k) / len(z)
            rows.append({"family": fam, "k": k, "n": len(z), "ari": round(ari, 3), "silhouette": round(sil, 3),
                         "smallest_pct": round(100 * size.min(), 1), "largest_pct": round(100 * size.max(), 1)})
            print(rows[-1], flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "bert_sweep.csv", index=False)
    (DATA / "bert_sweep.txt").write_text("K sweep for k-means on BERT pronoun vectors (PCA 50; 5 seeds, n_init=1 each)\n"
                                         "ari = mean adjusted Rand index between seeds; silhouette on 10,000 uses\n\n"
                                         + out.to_string(index=False) + "\n", encoding="utf-8")


def sentence(text, s, e, width=150):
    """The sentence holding text[s:e], with the word marked [[like this]]; long sentences trimmed around it."""
    cut = max(text.rfind(". ", 0, s), text.rfind("? ", 0, s), text.rfind("! ", 0, s))
    a = cut + 2 if cut >= 0 else 0
    m = re.search(r"[.!?](\s|$)", text[e:])
    b = e + m.end() if m else len(text)
    left, right = text[max(a, s - width):s], text[e:min(b, e + width)]
    return (("…" if s - width > a else "") + left + "[[" + text[s:e] + "]]" + right + ("…" if e + width < b else "")).strip()


def neighbours(text, s, e):
    prev = WORD.findall(text[max(0, s - 40):s].lower())
    nxt = WORD.findall(text[e:e + 40].lower())
    return (prev[-1] if prev else "<start>"), (nxt[0] if nxt else "<end>")


def log_odds(counts, labels, k, min_count=20):
    """Words most typical of each cluster vs the rest: log-odds with an informative Dirichlet prior
    (Monroe et al., 2008; prior 0.1 x the overall counts, as in Step 10). Returns {cluster: [(word, z), ...]}."""
    df = pd.DataFrame({"w": counts, "c": labels})
    tot = df.w.value_counts()
    keep = tot[tot >= min_count].index
    alpha = 0.1 * tot[keep]
    a0, out = alpha.sum(), {}
    for c in range(k):
        yc = df[df.c == c].w.value_counts().reindex(keep, fill_value=0)
        yr = tot[keep] - yc
        nc, nr = yc.sum(), yr.sum()
        d = np.log((yc + alpha) / (nc + a0 - yc - alpha)) - np.log((yr + alpha) / (nr + a0 - yr - alpha))
        z = d / np.sqrt(1 / (yc + alpha) + 1 / (yr + alpha))
        out[c] = [(w, round(v, 1)) for w, v in z.sort_values(ascending=False).head(8).items()]
    return out


def sheets(k_i, k_we):
    """Fit the chosen K, save every pronoun's cluster, and write reading sheets with no names or tiers."""
    from sklearn.cluster import KMeans
    text = answers()
    SHEETS.mkdir(exist_ok=True)
    saved = []
    for fam, k in [("i", k_i), ("we", k_we)]:
        sub, x = load_vectors(fam)
        z = reduce(x)
        km = KMeans(k, n_init=10, random_state=0).fit(z)
        order = np.argsort(-np.bincount(km.labels_, minlength=k))          # number clusters by size, largest first
        relabel = {old: new for new, old in enumerate(order)}
        lab = np.array([relabel[c] for c in km.labels_])
        cent = km.cluster_centers_[order]
        dist = np.linalg.norm(z - cent[lab], axis=1)
        nb = [neighbours(text[r], s, e) for r, s, e in zip(sub.row, sub.start, sub.end)]
        before = log_odds([p for p, _ in nb], lab, k)
        after = log_odds([n for _, n in nb], lab, k)
        rng = np.random.default_rng(1)
        lines = [f"# \"{FAMILY_NAME[fam]}\" clusters (K = {k}): reading sheet", "",
                 "No player names or tiers. [[ ]] marks the counted word. Name each cluster by how the pronoun is used,",
                 "then put it on a side: self / team / neither (rules in the Step 17 Doc tab).", ""]
        purity = [f"# \"{FAMILY_NAME[fam]}\" clusters: purity check (20 more random uses per cluster)", ""]
        for c in range(k):
            members = np.where(lab == c)[0]
            typical = members[np.argsort(dist[members])[:20]]
            pick = rng.permutation(members)
            rand, extra = pick[:20], pick[20:40]
            show = lambda ids: [f"{j + 1}. {sentence(text[sub.row[i]], sub.start[i], sub.end[i])}" for j, i in enumerate(ids)]
            lines += [f"## Cluster {c + 1}  ({100 * len(members) / len(sub):.1f}% of \"{FAMILY_NAME[fam]}\" uses, n = {len(members):,})", "",
                      "Words just before: " + ", ".join(f"{w} ({v})" for w, v in before[c]),
                      "Words just after: " + ", ".join(f"{w} ({v})" for w, v in after[c]), "",
                      "Most typical:", *show(typical), "", "Random:", *show(rand), "", "Name: ______   Side: self / team / neither", ""]
            purity += [f"## Cluster {c + 1}", "", *show(extra), "", "Fits the name: __ of 20", ""]
        (SHEETS / f"{fam}_clusters.md").write_text("\n".join(lines), encoding="utf-8")
        (SHEETS / f"{fam}_purity.md").write_text("\n".join(purity), encoding="utf-8")
        saved.append(pd.DataFrame({"pid": sub.pid, "family": fam, "cluster": lab + 1}))
        print(f"{fam}: K = {k}, sizes", np.bincount(lab).tolist())
    pd.concat(saved).sort_values("pid").to_csv(CLUSTERS, index=False)


# ------------------------------------------------------------------ deflections: nearest neighbours of seed examples
SEED = re.compile(r"\b(?:it|this|that)(?:'s| is| was)? (?:not|n't|never|isn't|wasn't)\s*(?:about|on|all about|just about)\s+(me|myself)\b"
                  r"|\b(?:it|this)(?:'s| is| was) not me\b|\bnot (?:just|only) me\b", re.I)   # deflection_check.py without bare "not me"


def search(top=300):
    a = pd.read_csv(DATA / "answers_analysis.csv", usecols=["person", "season", "tier", "answer"])
    a = a[a.tier.isin(TIERS)].reset_index(drop=True)
    text = a.answer.map(clean).tolist()
    sub, x = load_vectors("i")
    by_row = sub.groupby("row").indices
    seeds = []
    kobe = a.index[(a.person == "Kobe Bryant") & (a.season == 2008) & a.answer.str.startswith("I honestly don't believe")]
    for r in kobe:
        seeds += [i for i in by_row.get(r, []) if sub.word[i] == "me"]
    for r, t in enumerate(text):
        for m in SEED.finditer(t):
            seeds += [i for i in by_row.get(r, []) if m.start() <= sub.start[i] < m.end() and sub.word[i] in ("me", "myself")]
    seeds = sorted(set(seeds))
    sim = x @ x[seeds].mean(0)
    sim[seeds] = -np.inf
    best = np.argsort(-sim)[:top]
    lines = [f"Nearest neighbours of {len(seeds)} seed deflections (Kobe 2008 \"It is not me at the forefront\" + "
             f"\"it's not about/just me\" phrases), cosine similarity on BERT vectors (word-form means removed).",
             "Read each band of 40 and count real deflections (credit or focus pushed away from the speaker).", ""]
    for rank, i in enumerate(best):
        if rank % 40 == 0:
            lines += ["", f"--- ranks {rank + 1} to {rank + 40}   real deflections: __ of 40", ""]
        lines.append(f"{rank + 1}. ({sim[i]:.3f}) {sentence(text[sub.row[i]], sub.start[i], sub.end[i])}")
    SHEETS.mkdir(exist_ok=True)
    (SHEETS / "deflection_search.md").write_text("\n".join(lines), encoding="utf-8")
    pd.concat([pd.DataFrame({"pid": sub.pid[seeds], "rank": 0, "sim": 1.0}),            # rank 0 = the seeds themselves
               pd.DataFrame({"pid": sub.pid[best], "rank": np.arange(1, len(best) + 1), "sim": sim[best]})]).to_csv(
        DATA / "bert_deflection_search.csv", index=False)
    print(f"{len(seeds)} seeds; top similarity {sim[best[0]]:.3f}, rank {top} {sim[best[-1]]:.3f}")


# ------------------------------------------------------------------ check: the 90 hand-coded "we" uses (Step 12)
def wecheck():
    a = pd.read_csv(DATA / "answers_analysis.csv", usecols=["interview_id", "turn", "person", "tier", "answer"])
    a = a[a.tier.isin(TIERS)].reset_index(drop=True)
    key = {(i, t, p): r for r, (i, t, p) in enumerate(zip(a.interview_id, a.turn, a.person))}
    idx = pd.read_csv(IDX)
    idx["pid"] = np.arange(len(idx))
    cl = pd.read_csv(CLUSTERS).set_index("pid").cluster
    s = pd.read_csv(DATA / "we_sample.csv")
    found = []
    for _, x in s.iterrows():
        r = key.get((x.interview_id, x.turn, x.person))
        ctx = clean(x.context)
        k = ctx.find("[[")
        plain = ctx.replace("[[", "").replace("]]", "")
        text = clean(a.answer[r]) if r is not None else ""
        pos = text.find(plain)
        if r is None or pos < 0:
            found.append(None)
            continue
        at = pos + k
        hit = idx[(idx.row == r) & (idx.start == at) & (idx.family == "we")]
        found.append(int(cl[hit.pid.iat[0]]) if len(hit) else None)
    s["cluster"] = found
    tab = pd.crosstab(s.cluster, s.referent, margins=True)
    out = (f"The 90 hand-coded \"we\" uses (Step 12) by BERT \"we\" cluster; matched {s.cluster.notna().sum()} of {len(s)}\n\n"
           + tab.to_string() + "\n")
    (DATA / "bert_wecheck.txt").write_text(out, encoding="utf-8")
    print(out)


# ------------------------------------------------------------------ supervised: the labelling sample
LABEL = DATA / "bert_label"


def context2(text, s, e, width=260):
    """The sentence before and the sentence holding text[s:e] (word marked [[like this]]), trimmed."""
    def start_of(i):
        cut = max(text.rfind(". ", 0, i), text.rfind("? ", 0, i), text.rfind("! ", 0, i))
        return cut + 2 if cut >= 0 else 0
    a = start_of(s)
    p = start_of(a - 2) if a > 0 else a
    m = re.search(r"[.!?](\s|$)", text[e:])
    b = e + m.end() if m else len(text)
    left = text[max(p, s - width):s]
    right = text[e:min(b, e + width)]
    return (("…" if s - width > p else "") + left + "[[" + text[s:e] + "]]" + right + ("…" if e + width < b else "")).strip()


def labelsheet():
    """300 random "I" + 60 from the deflection search, 300 random "we" + 60 from "we" cluster 6; shuffled within family.
    Writes data/bert_label/sample.csv (the key) and data/bert_label/label_tool.html (no names, no tiers, no sources)."""
    import json
    LABEL.mkdir(exist_ok=True)
    text = answers()
    idx = pd.read_csv(IDX)
    idx["pid"] = np.arange(len(idx))
    cl = pd.read_csv(CLUSTERS).set_index("pid").cluster
    hits = pd.read_csv(DATA / "bert_deflection_search.csv")
    rng = np.random.default_rng(17)
    parts = []
    for fam, extra_pool, extra_src in [("i", hits.pid[hits["rank"].between(1, 300)].values, "search"),
                                       ("we", idx.pid[(idx.family == "we") & (idx.pid.map(cl) == 6)].values, "we_cluster6")]:
        pool = idx.pid[idx.family == fam].values
        rand = rng.choice(pool, 300, replace=False)
        extra = rng.choice(np.setdiff1d(extra_pool, rand), 60, replace=False)
        d = pd.DataFrame({"pid": np.r_[rand, extra], "source": ["random"] * 300 + [extra_src] * 60})
        parts.append(d.sample(frac=1, random_state=17).assign(family=fam))
    s = pd.concat(parts, ignore_index=True)
    s["lid"] = np.arange(1, len(s) + 1)
    s = s.merge(idx[["pid", "row", "start", "end", "word", "person", "tier"]], on="pid", how="left").sort_values("lid")
    s["context"] = [context2(text[r], a, b) for r, a, b in zip(s.row, s.start, s.end)]
    # 100 of the random uses for Claude's independent labels
    s["claude"] = s.lid.isin(rng.choice(s.lid[s.source == "random"].values, 100, replace=False))
    s[["lid", "pid", "family", "source", "word", "person", "tier", "claude", "context"]].to_csv(LABEL / "sample.csv", index=False)
    items = [{"id": int(r.lid), "f": r.family, "c": r.context} for r in s.itertuples()]
    html = (Path(__file__).resolve().parent / "label_tool_template.html").read_text(encoding="utf-8")
    (LABEL / "label_tool.html").write_text(html.replace("/*ITEMS*/[]", json.dumps(items, ensure_ascii=False)), encoding="utf-8")
    print(s.groupby(["family", "source"]).size().to_string())


# ------------------------------------------------------------------ supervised: agreement, classifier, labels for every use
PRED = DATA / "bert_pronoun_pred.csv"


def kappa(a, b):
    from sklearn.metrics import cohen_kappa_score
    return cohen_kappa_score(a, b)


def train(labels_file, coder="AI agent"):
    """Training labels (the blind AI agent's, data/bert_label/labels_agent.csv) -> logistic regression on the BERT
    vectors (5-fold CV split by player) -> a label for every use. Agreement with the other coders on their 100 items."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
    from sklearn.model_selection import StratifiedGroupKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    s = pd.read_csv(LABEL / "sample.csv")
    t = pd.read_csv(labels_file).rename(columns={"label": "y"})
    s = s.merge(t[["lid", "y"]], on="lid", how="left")
    lines = [f"Step 17 supervised: {s.y.notna().sum()} of {len(s)} uses labelled by the {coder} (training labels)", ""]

    others = {"Claude": LABEL / "labels_claude.csv", "AI agent 2": LABEL / "labels_agent2_check.csv", "Travis": LABEL / "labels_travis_check.csv"}
    coders = {coder: s[["lid", "family", "y"]].dropna()}
    for name, f in others.items():
        if f.exists():
            coders[name] = pd.read_csv(f).rename(columns={"label": "y"})[["lid", "family", "y"]]
    names = list(coders)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            m = coders[a].merge(coders[b], on=["lid", "family"], suffixes=("_a", "_b")).merge(s[["lid", "source"]], on="lid")
            m["part"] = np.where(m.source == "random", "random", "targeted")
            for (fam, part), d in m.groupby(["family", "part"]):
                if len(d):
                    lines.append(f"Agreement, {a} vs {b}, \"{FAMILY_NAME[fam]}\", {part} ({len(d)} uses): {100 * (d.y_a == d.y_b).mean():.0f}%, "
                                 f"Cohen's kappa {kappa(d.y_a, d.y_b):.2f}")
                    lines.append(pd.crosstab(d.y_a.rename(a), d.y_b.rename(b)).to_string())
    lines.append("")

    vec = np.load(VEC, mmap_mode="r")
    idx = pd.read_csv(IDX)
    pred_parts = []
    for fam in ["i", "we"]:
        d = s[(s.family == fam) & s.y.notna()].reset_index(drop=True)
        X, y, g = np.asarray(vec[d.pid.values], dtype=np.float32), d.y.values, d.person.values
        cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=0)
        best = None
        for C in [0.01, 0.1, 1.0]:
            oof = np.empty(len(y), dtype=object)
            for tr, te in cv.split(X, y, g):
                m = make_pipeline(StandardScaler(), LogisticRegression(C=C, class_weight="balanced", max_iter=3000))
                oof[te] = m.fit(X[tr], y[tr]).predict(X[te])
            f1 = f1_score(y, oof, average="macro")
            lines.append(f"\"{FAMILY_NAME[fam]}\" C = {C}: accuracy {accuracy_score(y, oof):.3f}, macro-F1 {f1:.3f}")
            if best is None or f1 > best[1]:
                best = (C, f1, oof)
        C, f1, oof = best
        rnd = (d.source == "random").values
        maj = pd.Series(y[rnd]).value_counts(normalize=True).iloc[0]
        acc_r, f1_r = accuracy_score(y[rnd], oof[rnd]), f1_score(y[rnd], oof[rnd], average="macro")
        ok = f1 >= 0.60 and acc_r > maj
        labs = sorted(set(y))
        lines += [f"chosen C = {C}; held-out players: macro-F1 {f1:.3f} (all labelled), random part: accuracy {acc_r:.3f} "
                  f"vs majority class {maj:.3f}, macro-F1 {f1_r:.3f}  ->  {'PASSES' if ok else 'FAILS'} the bar (macro-F1 >= 0.60 and above majority)",
                  "confusion (rows = training labels, columns = model, held-out):",
                  pd.DataFrame(confusion_matrix(y, oof, labels=labs), index=labs, columns=labs).to_string(),
                  f"label shares in the random sample (training labels): " + ", ".join(f"{k} {v:.0%}" for k, v in pd.Series(y[rnd]).value_counts(normalize=True).items()), ""]
        m = make_pipeline(StandardScaler(), LogisticRegression(C=C, class_weight="balanced", max_iter=3000)).fit(X, y)
        rows = np.where(idx.family.values == fam)[0]
        out = []
        for b in range(0, len(rows), 20000):
            out.append(m.predict(np.asarray(vec[rows[b:b + 20000]], dtype=np.float32)))
        pred = np.concatenate(out)
        lines.append(f"all \"{FAMILY_NAME[fam]}\" uses labelled by the model: " +
                     ", ".join(f"{k} {v:.1%}" for k, v in pd.Series(pred).value_counts(normalize=True).items()) + "\n")
        pred_parts.append(pd.DataFrame({"pid": rows, "family": fam, "label": pred, "passes": ok}))
    pd.concat(pred_parts).to_csv(PRED, index=False)
    (DATA / "bert_classifier.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


# ------------------------------------------------------------------ the corrected measure and the tier comparison
def model(source="classifier", defl_rank=0):
    """Context-corrected we-share = team-side / (self-side + team-side) per unit.
    source "classifier": sides from the trained classifier (data/bert_pronoun_pred.csv; "we" not_team -> neither).
    source "clusters": sides from data/bert_sides.csv (family, cluster, name, side); defl_rank > 0 moves the seeds
    and the deflection-search hits up to that rank to the team side."""
    import models as M
    idx = pd.read_csv(IDX)
    idx["pid"] = np.arange(len(idx))
    idx = idx.merge(pd.read_csv(CLUSTERS)[["pid", "cluster"]], on="pid")
    if source == "classifier":
        pr = pd.read_csv(PRED)
        assert pr[pr.family == "i"].passes.all(), "the \"I\" classifier did not pass the bar; report that instead"
        # a classifier that fails the bar is not used: those uses keep the original treatment ("we" = team)
        pr.loc[(pr.family == "we") & ~pr.passes, "label"] = "team"
        idx = idx.merge(pr[["pid", "label"]], on="pid")
        idx["name"] = idx.family + ":" + idx.label
        idx["side"] = idx.label.replace({"not_team": "neither"})
        sides = idx.groupby(["family", "label"]).size().rename("uses").reset_index()
    else:
        sides = pd.read_csv(DATA / "bert_sides.csv")
        idx = idx.merge(sides[["family", "cluster", "name", "side"]], on=["family", "cluster"], how="left")
    assert idx.side.isin(["self", "team", "neither"]).all(), "every use needs a side"
    if defl_rank:
        hits = pd.read_csv(DATA / "bert_deflection_search.csv")
        idx.loc[idx.pid.isin(hits.pid[hits["rank"] <= defl_rank]), ["side", "name"]] = ["team", "deflecting (search)"]
    a = pd.read_csv(DATA / "answers_analysis.csv", usecols=["tier", "person_key"])
    a = a[a.tier.isin(TIERS)].reset_index(drop=True)
    idx["person_key"] = a.person_key.values[idx.row]
    cnt = idx.groupby(["interview_id", "person_key", "side"]).size().unstack(fill_value=0)
    cnt = cnt.reindex(columns=["self", "team", "neither"], fill_value=0).add_prefix("c_").reset_index()
    cnt = cnt.rename(columns={"c_interview_id": "interview_id", "c_person_key": "person_key"})

    u = M.load().merge(cnt, on=["interview_id", "person_key"], how="left")
    u[["c_self", "c_team", "c_neither"]] = u[["c_self", "c_team", "c_neither"]].fillna(0)
    d = u[(u.c_self + u.c_team) > 0].assign(st=lambda x: x.c_self + x.c_team, pron=lambda x: x.i_count + x.we_count)
    lines = [f"Step 17: context-corrected we-share = team side / (self side + team side); sides from: {source}; deflection search ranks used: {defl_rank or 'none'}",
             f"units with any self- or team-side pronoun: {len(d):,} of {len(u):,}; players {d.person_key.nunique()}", "",
             "Sides:", sides.to_string(index=False), "",
             "Pronouns by side: " + ", ".join(f"{k} {v:,}" for k, v in idx.side.value_counts().items()), ""]
    raw = d.assign(cws=d.c_team / d.st, ws=d.we_count / d.pron).groupby("tier")[["cws", "ws"]].agg(["mean", "median"]).loc[TIERS]
    lines += ["Raw unit averages (cws = corrected, ws = original we-share):", raw.round(3).to_string(), ""]

    effects = []

    def record(analysis, spec, res, X, data):
        e = M.tier_effects(res, X, "binomial")
        e.insert(0, "spec", spec)
        e.insert(0, "analysis", analysis)
        e["n_units"], e["n_players"] = len(data), data.person_key.nunique()
        effects.append(e)
        lines.append(f"--- {analysis} | {spec} | units {len(data)}, players {data.person_key.nunique()}")
        for _, r in e.iterrows():
            s = f"  {r.tier:<10} {r.estimate:7.3f} [{r.lo:.3f}, {r.hi:.3f}]"
            if r.tier != "role":
                s += f"   vs role {r['diff']:+.3f} [{r.diff_lo:+.3f}, {r.diff_hi:+.3f}]  OR {r.ratio:.2f}  p={r.p:.3f}"
            lines.append(s)

    for spec, ctrl in M.LADDER.items():
        res, X = M.fit(d, "c_team", ctrl, denom="st")
        record("A corrected we-share", spec, res, X, d)
    res, X = M.fit(d, "we_count", M.LADDER[M.FULL], denom="pron")
    record("A original we-share, same units", M.FULL, res, X, d)
    tot = d.groupby("person_key")[["c_self", "c_team"]].sum()
    b = d[d.person_key.isin(tot[(tot.c_self > 0) & (tot.c_team > 0)].index)]
    res, X = M.fit(b, "c_team", M.LADDER[M.FULL], fe=True, denom="st")
    record("B corrected we-share, same player (FE)", M.FULL, res, X, b)

    # the mix of "I" uses in each tier: pooled, and with each player counted once
    ii = idx[idx.family == "i"].copy()
    ii["label"] = ii.name.astype(str) if source == "classifier" else ii.cluster.astype(str) + " " + ii.name.astype(str)
    pooled = pd.crosstab(ii.tier, ii.label, normalize="index").loc[TIERS]
    per_player = (pd.crosstab([ii.tier, ii.person_key], ii.label, normalize="index").groupby(level=0).mean().loc[TIERS])
    lines += ["", "Mix of \"I\" uses by tier (share of each tier's \"I\" words), pooled:", (100 * pooled).round(1).T.to_string(),
              "", "Same, each player counted once (mean of player shares):", (100 * per_player).round(1).T.to_string()]
    pd.concat(effects).to_csv(DATA / "bert_effects.csv", index=False)
    (100 * pooled).round(2).T.to_csv(DATA / "bert_i_mix.csv")
    (DATA / "bert_results.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "embed":
        embed(int(sys.argv[2]) if len(sys.argv) > 2 else None)
    elif cmd == "sweep":
        sweep()
    elif cmd == "sheets":
        sheets(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "search":
        search()
    elif cmd == "wecheck":
        wecheck()
    elif cmd == "labelsheet":
        labelsheet()
    elif cmd == "train":
        train(sys.argv[2])
    elif cmd == "model":
        model(sys.argv[2] if len(sys.argv) > 2 else "classifier", int(sys.argv[3]) if len(sys.argv) > 3 else 0)
    else:
        print(__doc__)
