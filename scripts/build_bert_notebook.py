"""Builds and runs notebooks/02_bert_pronouns.ipynb: the Step 17 results (BERT, "I" and "we" read in context).
It only reads the saved outputs of scripts/bert_pronouns.py; nothing is refitted.

    cd scripts && python build_bert_notebook.py
"""
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell

cells = [
    md("# Step 17: reading \"I\" and \"we\" in context (BERT)\n\n"
       "Exploratory, added after the main analysis was frozen. The we-share counts words, not meaning: in Kobe Bryant's "
       "\"It is not me at the forefront\", *me* counts as self-focus although he is giving the credit away. Here every counted "
       "\"I\" and \"we\" gets a contextual embedding from `bert-base-uncased`, and a classifier sorts each one into **self**, "
       "**team** or **neither** (conversation). The tier comparison is then rerun on a context-corrected we-share.\n\n"
       "**All labels in this step come from AI models** (a blind labelling agent, checked by a second blind agent and by Claude); "
       "there is no human check. Method, rules and prediction were written in the Doc tab *Step 17* before any tier result.\n\n"
       "Pipeline: `scripts/bert_pronouns.py` (embed, sweep, sheets, search, wecheck, labelsheet, train, model). "
       "This notebook only reads its saved outputs."),
    code("import pandas as pd\nimport matplotlib.pyplot as plt\nfrom pathlib import Path\n"
         "DATA = Path('..') / 'data'\npd.set_option('display.width', 140)"),
    md("## 1. The embeddings\n\n219,191 vectors (111,278 \"I\", 107,913 \"we\"): one per word the we-share counts, the mean of BERT's last four "
       "layers over the word's pieces, with the whole answer as context. The counts were checked to equal `i_count` and `we_count`."),
    code("idx = pd.read_csv(DATA / 'bert_pronoun_index.csv')\nidx.groupby(['family', 'word']).size().rename('uses').to_frame().T"),
    md("## 2. Clustering first (descriptive)\n\nk-means on the vectors (word-form means removed, PCA 50). Stability across 5 seeds "
       "(adjusted Rand index) and silhouette by K:"),
    code("pd.read_csv(DATA / 'bert_sweep.csv')"),
    md("Silhouette stays at 0.05 to 0.08 for every K: the uses do not form separate groups. Reading the clusters (sheets in "
       "`data/bert_sheets/`) showed that they split by grammar and position (\"I think\" + a statement, \"I mean\", \"like I said\", "
       "\"my / myself\"), not by self against team, and the 10 non-team \"we\" from the Step 12 check spread over four \"we\" clusters:"),
    code("print((DATA / 'bert_wecheck.txt').read_text(encoding='utf-8'))"),
    md("So the main measure became **supervised**: label examples, train a classifier, label every use."),
    md("## 3. Labels and agreement\n\n720 uses (300 random + 60 targeted for each word type), labelled blind by an AI agent. "
       "A second blind agent labelled 220 of them (the 100 random ones Claude also labelled, and the 120 targeted ones). "
       "Agreement:"),
    code("log = (DATA / 'bert_train.log').read_text(encoding='utf-8')\n"
         "print('\\n'.join(l for l in log.splitlines() if l.startswith('Agreement')))"),
    md("Near-perfect on ordinary uses; lower on the targeted rare kinds of \"I\" (kappa 0.65), mostly a player naming himself in a "
       "list with teammates (self or team?). Team-type \"I\" is about 3% of all \"I\", so this boundary moves the measure little."),
    md("## 4. The classifier\n\nLogistic regression on the 768 BERT numbers, 5-fold cross-validation split by player (always tested "
       "on players it never saw). The bar, written in advance: macro-F1 at least 0.60 and accuracy above always guessing the most "
       "common label."),
    code("print('\\n'.join(l for l in log.splitlines() if l.startswith(('chosen', 'all \"', 'label shares'))))"),
    md("\"I\" passes. \"We\" fails (0.94 against 0.95 for calling every \"we\" team), so it is not used and every \"we\" counts as "
       "team, as in the original measure.\n\n**Context-corrected we-share** = (team \"I\" + all \"we\") / (self \"I\" + team \"I\" + all \"we\"): "
       "conversational \"I\" is left out and credit-giving \"I\" moves to the team side."),
    md("## 5. How \"I\" is used, by tier"),
    code("mix = pd.read_csv(DATA / 'bert_i_mix.csv', index_col=0)\nmix.index = mix.index.str.replace('i:', '')\n"
         "mix.round(1)  # % of each tier's \"I\" words, pooled"),
    md("About 38% of \"I\" words are conversation in every tier. Counting them as self-focus added noise, not a difference "
       "between tiers."),
    md("## 6. The tier comparison"),
    code("e = pd.read_csv(DATA / 'bert_effects.csv')\n"
         "s = e[e.tier == 'superstar'][['analysis', 'spec', 'diff', 'diff_lo', 'diff_hi', 'p', 'n_units', 'n_players']].copy()\n"
         "for c in ['diff', 'diff_lo', 'diff_hi']:\n    s[c] = (100 * s[c]).round(1)\n"
         "s.rename(columns={'diff': 'superstar - role (points)', 'diff_lo': 'lo', 'diff_hi': 'hi'})"),
    code("rows = [('Original we-share\\n(main model)', 'A original we-share, same units'),\n"
         "        ('Context-corrected\\n(main model)', 'A corrected we-share'),\n"
         "        ('Context-corrected\\n(same player)', 'B corrected we-share, same player (FE)')]\n"
         "full = s[s.spec == '4 + question topics'].set_index('analysis')\n"
         "fig, ax = plt.subplots(figsize=(7.5, 3.2))\n"
         "for k, (label, key) in enumerate(rows):\n"
         "    r = full.loc[key]\n"
         "    ax.plot([r.diff_lo, r.diff_hi], [k, k], color='#2a78d6', lw=2.5, solid_capstyle='round')\n"
         "    ax.plot(r['diff'], k, 'o', color='#2a78d6', ms=9, mec='white', mew=2)\n"
         "    ax.text(r.diff_hi + 0.4, k, f\"{r['diff']:+.1f} [{r.diff_lo:+.1f}, {r.diff_hi:+.1f}]\", va='center', fontsize=10)\n"
         "ax.axvline(0, color='0.5', lw=1)\nax.set_yticks(range(len(rows)), [r[0] for r in rows])\nax.invert_yaxis()\n"
         "ax.set_xlim(-8, 11)\nax.set_xlabel('Superstar minus role player, share of \"we\" (percentage points), 95% CI')\n"
         "for sp in ['top', 'right']:\n    ax.spines[sp].set_visible(False)\n"
         "ax.grid(axis='x', color='0.9')\nax.set_axisbelow(True)\nfig.tight_layout()\n"
         "fig.savefig(Path('..') / 'figures' / 'bert_superstar_vs_role.png', dpi=200)\nplt.show()"),
    md("## Reading\n\nThe null holds when \"I\" and \"we\" are read in context: superstar minus role is about zero on the original "
       "we-share (-0.4 points) and on the context-corrected one (-0.5 points, 95% CI -4.5 to +3.6; same player +0.9). The prediction "
       "(superstars higher) is not supported. Limits: exploratory and added after the freeze; every label comes from AI models with no "
       "human check; the classifier finds only about half of the rare credit-giving \"I\"; the \"we\" classifier was not used."),
    md("## 7. Step 18: the BERT measure becomes the main measure\n\nOn 18 Nov the context-corrected measure (\"team-focused share\") was made "
       "the main measure of the talk, after both main results were known; they agree. The situation effects and the 14 Step 9 robustness checks were "
       "rerun on it with `scripts/bert_main.py`, which reuses the existing model code with the counts swapped (self \"I\" for \"I\", team side for "
       "\"we\") and first checks that it reproduces the Step 17 result exactly."),
    code("txt = (DATA / 'bert_main_results.txt').read_text(encoding='utf-8')\n"
         "print(txt.split('Robustness')[0])"),
    code("rb = pd.read_csv(DATA / 'bert_robustness.csv')[['group', 'check', 'diff', 'diff_lo', 'diff_hi', 'p', 'n_units', 'n_players']]\n"
         "for c in ['diff', 'diff_lo', 'diff_hi']:\n    rb[c] = (100 * rb[c]).round(1)\n"
         "rb.round({'p': 3})  # superstar minus role, points of team-focused share"),
    md("Same conclusion on the main measure: 13 of 14 checks include zero; the exception is again game days only (+6.2 points), where role "
       "players speak after their own big games (+5.3 points above their own average)."),
]

nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
out = ROOT / "notebooks" / "02_bert_pronouns.ipynb"
NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(out.parent)}}).execute()
nbf.write(nb, out)
print("wrote", out)
