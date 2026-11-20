# HG4054-Project

**Are superstars more self-focused than role players?** Final project for NTU HG4054 (Data Analytics/NLP): "I" versus "we" in 4,058 NBA playoff press conferences, 2004–2026.

## What's here

- `scripts/`: scraping, cleaning, models and checks in Python. The run order and each script's outputs are listed in `CLAUDE.md` under "Project files".
- `data/`: derived results (model outputs, robustness checks, topic shares, labels).
- `figures/`, `notebooks/`: figures and results notebooks.
- `presentation/`: the talk deck, a Next.js site. Run `cd presentation && npm install && npm run build && npx next start -p 3054`. `presentation/TALK_SCRIPT.md` is the talk script.
- `requirements_frozen.txt`: Python package versions.

## Not included

- **ASAP Sports transcripts:** the raw pages and the tables that hold their full text (`asap_nba_answers.csv`, `answers_analysis.csv`, `answers_labeled.csv`, `units.csv`). To rebuild them, run `python scripts/scrape_asap.py fetch`, then `parse`, then `cd scripts && python build_analysis_data.py`. `answers_labeled.csv` comes from `notebooks/01_eda_labels.ipynb`.
- **NBA.com player headshots:** not licensed for publishing, so the deck's player photos are missing.
- **Raw downloads and caches:** the nba_api and Wikipedia downloads, the BERT and MiniLM embedding caches (`*.npy`) and the dated snapshots.
