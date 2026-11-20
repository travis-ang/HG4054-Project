"""Summarise and sanity-check data/asap_nba_answers.csv.

python scripts/summarize_data.py

Writes:
  data/data_summary.txt   counts by year, round and speaker, plus quality checks
  data/sample_check.txt   30 random answers to read by hand
"""
import random
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "asap_nba_answers.csv"
SUMMARY = ROOT / "data" / "data_summary.txt"
SAMPLE = ROOT / "data" / "sample_check.txt"

df = pd.read_csv(CSV, dtype=str, keep_default_na=False)
df["n_words"] = df["n_words"].astype(int)

# A speaker label that matches one of the names listed in the transcript header
# is a known interviewee; anything else (THE MODERATOR, typos) needs a look.
def listed(row):
    names = [n.strip().upper() for n in row["listed_speakers"].split(";") if n.strip()]
    return any(row["speaker"].upper() == n or row["speaker"].upper() in n or n in row["speaker"].upper()
               for n in names)

df["speaker_in_header"] = df.apply(listed, axis=1)
df["is_moderator"] = df["speaker"].str.contains("MODERATOR", case=False)

out = []
p = out.append
p("ASAP Sports NBA playoff transcripts: data summary\n")
p(f"Interviews: {df['interview_id'].nunique():,}")
p(f"Answer rows: {len(df):,}")
p(f"Distinct speaker labels: {df['speaker'].nunique():,}")
p(f"Total answer words: {df['n_words'].sum():,}")
p(f"Median words per answer: {df['n_words'].median():.0f}")
p(f"Years covered: {df['year'].min()} to {df['year'].max()}\n")

p("Interviews by year and round")
p(df.groupby(["year", "round"])["interview_id"].nunique().unstack(fill_value=0).to_string())
p("")

p("Answer rows by round")
p(df["round"].value_counts().to_string())
p("")

p("Answer rows by session type")
p(df["session"].value_counts().to_string())
p("")

p("Top 40 speakers by number of answers")
p(df["speaker"].value_counts().head(40).to_string())
p("")

p("Quality checks")
p(f"  Moderator rows: {df['is_moderator'].sum():,}")
p(f"  Rows labelled 'COACH ...': {(df['is_coach_label'] == '1').sum():,}")
p(f"  Answers containing leftover site footer text: {df['answer'].str.contains('FastScripts|ASAP Sports, Inc', regex=True).sum():,}")
p(f"  Rows whose speaker is not in the header list: {(~df['speaker_in_header']).sum():,}")
p(f"  Empty answers: {(df['n_words'] == 0).sum():,}")
p(f"  Answers with no preceding question (opening statements): {(df['question'] == '').sum():,}")
p(f"  Rows with leftover mojibake characters: {df['answer'].str.contains('Ã|â€', regex=True).sum():,}")
p("")
p("Most common speaker labels not found in the header (check these):")
p(df.loc[~df["speaker_in_header"], "speaker"].value_counts().head(30).to_string())

SUMMARY.write_text("\n".join(out), encoding="utf-8")

random.seed(4054)
rows = df.sample(30, random_state=4054)
with SAMPLE.open("w", encoding="utf-8") as f:
    for _, r in rows.iterrows():
        f.write(f"[{r['interview_id']}] {r['date']} | {r['event']} | {r['game_info']}\n")
        f.write(f"Header speakers: {r['listed_speakers']} | team: {r['listed_team']}\n")
        f.write(f"Q: {r['question']}\n{r['speaker']}: {r['answer']}\n{r['url']}\n\n")

print("\n".join(out[:8]))
print(f"\nWrote {SUMMARY} and {SAMPLE}")
