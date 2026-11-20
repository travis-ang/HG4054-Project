"use client";

import { motion } from "framer-motion";
import { CSSProperties } from "react";
import { Card, CountUp, Header, Reveal, Tip, usePick } from "@/components/ui";
import { a, C, ease, pct, R } from "@/lib/theme";
import { SlideProps } from "./types";

/* Step 19: two slides that explain BERT and the labelled data behind the main measure (numbers: results.json "bert_explain") */
const E = R.bert_explain;
type Kind = "self" | "neither" | "team";
const KINDS: { k: Kind; name: string; col: string }[] = [
  { k: "self", name: "self", col: C.i },
  { k: "neither", name: "conversation", col: C.dim },
  { k: "team", name: "team", col: C.we },
];
const KNAME = Object.fromEntries(KINDS.map((d) => [d.k, d.name])) as Record<Kind, string>;
const kick: CSSProperties = { fontSize: 22, letterSpacing: "0.14em", color: C.gold, fontWeight: 700 };
const POS = "#e9a93b", NEG = "#8fa3c4"; // above / below the average "I" (a diverging pair; near the average = no line)

/** A sentence with the read word marked. */
function Said({ tokens, col = C.i }: { tokens: { t: string; k: string }[]; col?: string }) {
  return (
    <>
      {tokens.map((tk, n) => tk.k === "target"
        ? <span key={n} style={{ color: col, background: a(col, 0.2), boxShadow: `inset 0 -3px 0 ${col}`, borderRadius: 6, padding: "0 4px", fontWeight: 700 }}>{tk.t}</span>
        : <span key={n}>{tk.t}</span>)}
    </>
  );
}

/** The 768 numbers of one word, one thin line each. */
function Barcode({ v, width, height, show, delay }: { v: number[]; width: number; height: number; show: boolean; delay: number }) {
  const w = width / v.length;
  return (
    <motion.svg width={width} height={height} style={{ display: "block", borderRadius: 4 }}
      initial={{ clipPath: "inset(0 100% 0 0)" }} animate={{ clipPath: show ? "inset(0 0% 0 0)" : "inset(0 100% 0 0)" }}
      transition={{ duration: 0.9, delay: show ? delay : 0, ease }}>
      <rect width={width} height={height} fill="rgba(246,239,228,0.04)" />
      {v.map((x, k) => (x === 0 ? null : (
        <rect key={k} x={k * w} width={w + 0.35} height={height} fill={x > 0 ? POS : NEG} fillOpacity={Math.min(Math.abs(x) / 2.5, 1)} />
      )))}
    </motion.svg>
  );
}

/** Cut a sentence's tokens after about n characters (at a token edge), adding "…"; the marked word is always kept. */
function cut(tokens: { t: string; k: string }[], n: number) {
  const out: { t: string; k: string }[] = [];
  let len = 0, seen = false;
  for (const tk of tokens) {
    if (len + tk.t.length > n && seen) return [...out, { t: " …", k: "" }];
    out.push(tk);
    len += tk.t.length;
    seen ||= tk.k === "target";
  }
  return out;
}

/* ------------------------------------------------------------------ 7. What is BERT? */
const SIM = E.similarity as Record<string, number>;
const simOf = (p: Kind, q: Kind) => SIM[`${p}-${q}`] ?? SIM[`${q}-${p}`];

const SETUP: [string, string][] = [
  ["Model", "bert-base-uncased, frozen"],
  ["Token vector", "mean of last 4 layers, 768-d"],
  ["Context", "full answer (510-piece windows)"],
  ["Tokens", `${E.n_i.toLocaleString("en-US")} “I” · ${(E.n_vectors - E.n_i).toLocaleString("en-US")} “we”`],
];

export function WhatBert({ step }: SlideProps) {
  const pick = usePick<Kind>(); // hover or click a sentence for its cosine similarities
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Measuring self-focus · contextual embeddings" title="BERT: a contextual embedding for every “I”" size={80} />
      {/* left: the setup, for replication */}
      <Reveal delay={0.25} style={{ position: "absolute", left: 110, top: 290, width: 640 }}>
        <Card style={{ padding: "26px 34px", height: 610 }}>
          <div className="font-cond" style={kick}>SETUP</div>
          {SETUP.map(([k, v], j) => (
            <Reveal key={k} delay={0.4 + j * 0.12} x={-16} y={0}>
              <div style={{ padding: "22px 0", borderBottom: j < SETUP.length - 1 ? `1px solid ${C.grid}` : undefined }}>
                <div className="font-cond" style={{ fontSize: 21, letterSpacing: "0.12em", color: C.muted, fontWeight: 700 }}>{k.toUpperCase()}</div>
                <div style={{ fontSize: 31, fontWeight: 600, marginTop: 4 }}>{v}</div>
              </div>
            </Reveal>
          ))}
          <div style={{ fontSize: 20, color: C.muted, marginTop: 10 }}>Devlin et al. (2019)</div>
        </Card>
      </Reveal>
      {/* right: the same word gets different vectors in different sentences; nearest neighbours share the use */}
      <Reveal show={step >= 1} style={{ position: "absolute", left: 790, top: 290, width: 1020 }}>
        <Card style={{ padding: "26px 34px", height: 610 }}>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
            <div className="font-cond" style={kick}>SAME TOKEN, DIFFERENT VECTORS</div>
            <div style={{ fontSize: 19, color: C.muted }}>768 dims, z-scored · nearest neighbour by cosine</div>
          </div>
          {KINDS.map(({ k }, j) => {
            const x = E.examples[k];
            const nb = x.neighbours[0];
            return (
              <motion.div key={k} className="tap" {...pick.bind(k)} animate={{ opacity: pick.active && pick.active !== k ? 0.35 : 1 }}
                style={{ padding: "16px 0 14px", marginTop: j ? 0 : 12, borderTop: `1px solid ${C.grid}` }}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 14, marginBottom: 8 }}>
                  <div style={{ fontSize: 27 }}>“<Said tokens={x.tokens} />”</div>
                  <div style={{ fontSize: 19, color: C.muted, whiteSpace: "nowrap" }}>{x.person} · {x.season}</div>
                </div>
                <Barcode v={x.vector} width={952} height={30} show={step >= 1} delay={0.3 + j * 0.2} />
                <motion.div initial={false} animate={{ opacity: step >= 2 ? 1 : 0 }} transition={{ delay: step >= 2 ? 0.2 + j * 0.2 : 0 }}
                  style={{ fontSize: 21, color: C.muted, marginTop: 8 }}>
                  NN: <span style={{ color: C.cream }}>“<Said tokens={cut(nb.tokens, 40)} />”</span> {nb.person}, {nb.season} ·{" "}
                  <b style={{ color: C.cream }}>{nb.similarity.toFixed(2)}</b>
                </motion.div>
              </motion.div>
            );
          })}
        </Card>
      </Reveal>
      {KINDS.map(({ k }, j) => {
        const x = E.examples[k];
        const others = KINDS.filter((d) => d.k !== k);
        return (
          <Tip key={k} show={step >= 1 && pick.active === k} x={1300} y={378 + j * 150} anchor="above" width={720}>
            <div style={{ fontSize: 21 }}>
              Cosine: NN ({x.neighbours[0].person}) <b>{x.neighbours[0].similarity.toFixed(2)}</b>
              {others.map((o) => <span key={o.k}> · {KNAME[o.k]} example <b>{simOf(k, o.k).toFixed(2).replace("-", "−")}</b></span>)}
              {" "}· NN searched over all {E.n_i.toLocaleString("en-US")} “I”, other players
            </div>
          </Tip>
        );
      })}
      <Reveal show={step >= 2} delay={0.7} style={{ position: "absolute", left: 110, top: 930, width: 1700 }}>
        <div style={{ fontSize: 26, textAlign: "center" }}>
          Neighbours share the use → <b style={{ color: C.gold }}>a linear classifier on the embeddings (next slide)</b>
        </div>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 8. The new data: labels and a classifier */
const STAGES = [
  { tag: "Embed", n: E.n_vectors, suf: "", unit: "“I” / “we” tokens, 768-d" },
  { tag: "Label", n: E.sample.total, suf: "", unit: `uses: ${E.sample.random_per_word} random + ${E.sample.targeted_per_word} targeted per word, blind AI coder` },
  { tag: "Test", n: E.i.accuracy * 100, suf: "%", unit: "accuracy on held-out players (“I”)" },
  { tag: "Predict", n: E.n_i, suf: "", unit: "“I” tokens classified" },
];
const CM = E.i_confusion;
const HC = R.human_check;   // Step 23: Travis's blind first pass on the 100 random uses
const STAGE_INFO = [
  <>{E.n_i.toLocaleString("en-US")} “I” + {(E.n_vectors - E.n_i).toLocaleString("en-US")} “we”: exactly the tokens the we-share counts.
    Mean of the last 4 hidden layers over word pieces; context = full answer.</>,
  <>Per family: {E.sample.random_per_word} random + {E.sample.targeted_per_word} targeted (NN search from credit-giving seeds; odd “we” cluster).
    Random “I”: self {pct(E.i.shares.self, 0)}%, conversation {pct(E.i.shares.neither, 0)}%, team {pct(E.i.shares.team, 0)}% · random “we”: team {pct(E.we.shares.team, 0)}%.</>,
  <>L2 logistic regression (standardised, class-balanced, C = {E.i.C}), stratified group 5-fold CV by player. Recall: self {CM.self.right}/{CM.self.total} ·
    conversation {CM.neither.right}/{CM.neither.total} · team <b>{CM.team.right}/{CM.team.total}</b>.</>,
  <>Per unit: counts of self, team and conversation “I” → team-focused share.</>,
];

export function BertLabels({ step }: SlideProps) {
  const X = (k: number) => 110 + k * 436;
  const W = 380;
  const pick = usePick<number>(); // hover or click a stage for its details
  const shown = (k: number) => (k < 2 ? true : step >= 1);
  const bar = [
    { w: "“I”", col: C.i, acc: E.i.accuracy, base: E.i.baseline, f1: E.i.macro_f1, ok: E.i.passes },
    { w: "“we”", col: C.we, acc: E.we.accuracy, base: E.we.baseline, f1: E.we.macro_f1, ok: E.we.passes },
  ];
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Measuring self-focus · L2 logistic regression on the embeddings" title="720 labelled uses train a classifier" />
      {STAGES.map((s, k) => (
        <Reveal key={k} show={shown(k)} delay={k < 2 ? 0.2 + k * 0.25 : 0.1 + (k - 2) * 0.25} y={36}
          style={{ position: "absolute", left: X(k), top: 290, width: W }}>
          <div className="tap" {...pick.bind(k)}>
            <Card style={{ height: 300, padding: "24px 28px" }} glow={pick.active === k ? C.gold : undefined}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span className="font-display" style={{ width: 44, height: 44, borderRadius: "50%", background: C.gold, color: C.ink,
                  display: "grid", placeItems: "center", fontSize: 30 }}>{k + 1}</span>
                <span className="font-cond" style={{ fontSize: 23, letterSpacing: "0.18em", fontWeight: 700, color: C.gold }}>{s.tag.toUpperCase()}</span>
              </div>
              <div className="font-display" style={{ fontSize: 92, lineHeight: 1, marginTop: 30, color: C.cream }}>
                <CountUp to={s.n} suffix={s.suf} show={shown(k)} />
              </div>
              <div style={{ fontSize: 26, fontWeight: 600, lineHeight: 1.25, marginTop: 8 }}>{s.unit}</div>
            </Card>
          </div>
        </Reveal>
      ))}
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
        {[0, 1, 2].map((k) => (
          <motion.path key={k} d={`M${X(k) + W + 8} 440 L${X(k + 1) - 10} 440 M${X(k + 1) - 22} 430 L${X(k + 1) - 10} 440 L${X(k + 1) - 22} 450`}
            stroke={C.gold} strokeWidth={4} fill="none" initial={{ opacity: 0 }} animate={{ opacity: shown(k + 1) ? 1 : 0 }}
            transition={{ delay: k === 0 ? 0.6 : 0.3 + (k - 1) * 0.25 }} />
        ))}
      </svg>
      {STAGES.map((_, k) => (
        <Tip key={k} show={shown(k) && pick.active === k} x={Math.min(Math.max(X(k) + W / 2, 420), 1500)} y={606} anchor="center" width={620}>
          <div style={{ fontSize: 21 }}>{STAGE_INFO[k]}</div>
        </Tip>
      ))}
      {/* bottom: checks on the labels, and the pass bar */}
      <Reveal show={step >= 2} style={{ position: "absolute", left: 110, top: 640, width: 830 }}>
        <Card style={{ height: 290, padding: "24px 32px" }}>
          <div className="font-cond" style={kick}>BLIND AGREEMENT WITH THE TRAINING LABELS · “I”</div>
          <div style={{ display: "flex", gap: 36, marginTop: 12 }}>
            {[{ v: E.agree.i_random.pct, t: "AI coder 2 · random", k: E.agree.i_random.kappa, n: E.agree.i_random.n, human: false },
              { v: E.agree.i_targeted.pct, t: "AI coder 2 · targeted", k: E.agree.i_targeted.kappa, n: E.agree.i_targeted.n, human: false },
              { v: HC.i.pct, t: "human · random", k: HC.i.kappa, n: HC.i.n, human: true }].map((s) => (
              <div key={s.t}>
                <div className="font-display" style={{ fontSize: 74, lineHeight: 1, color: s.human ? C.gold : C.cream }}>{s.v}%</div>
                <div style={{ fontSize: 21, color: s.human ? C.cream : C.muted, fontWeight: s.human ? 700 : 400 }}>{s.t}</div>
                <div style={{ fontSize: 19, color: C.muted }}>κ = {s.k.toFixed(2)} · n = {s.n}</div>
              </div>
            ))}
          </div>
          <div style={{ fontSize: 22, fontWeight: 700, color: C.gold, marginTop: 14 }}>
            Human check (blind, {HC.n} random uses): “we” {HC.we.pct}% · “I” vs classifier {HC.i_classifier.pct}%
          </div>
          <div style={{ fontSize: 20, color: C.muted }}>most “I” splits: framing verbs (“I think”, “I know”)</div>
        </Card>
      </Reveal>
      <Reveal show={step >= 2} delay={0.2} style={{ position: "absolute", left: 980, top: 640, width: 830 }}>
        <Card style={{ height: 290, padding: "24px 32px" }} glow={C.gold}>
          <div className="font-cond" style={kick}>PRE-SET BAR</div>
          <div style={{ fontSize: 20, color: C.muted, marginTop: 4 }}>accuracy &gt; majority baseline · macro-F1 ≥ 0.60 (held-out players)</div>
          {bar.map((b) => (
            <div key={b.w} style={{ display: "flex", alignItems: "center", gap: 20, marginTop: 18 }}>
              <span className="font-display" style={{ width: 76, fontSize: 48, color: b.col }}>{b.w}</span>
              <span style={{ fontSize: 26, flex: 1 }}>
                acc <b>{b.acc.toFixed(2)}</b> <span style={{ color: C.muted }}>vs {b.base.toFixed(2)} majority · F1 {b.f1.toFixed(2)}</span>
              </span>
              <span className="font-cond" style={{ fontSize: 23, fontWeight: 700, letterSpacing: "0.08em", padding: "4px 16px", borderRadius: 999,
                color: b.ok ? C.ink : C.cream, background: b.ok ? C.gold : "transparent", border: `2px solid ${b.ok ? C.gold : C.dim}` }}>
                {b.ok ? "✓ USED" : "✗ NOT USED"}
              </span>
            </div>
          ))}
        </Card>
      </Reveal>
    </div>
  );
}
