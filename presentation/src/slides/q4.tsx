"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import { Ball, Card, Header, Headshot, Kicker, Reveal, stop, TierPill, Tip, Title, usePick } from "@/components/ui";
import { a, C, lin, pct, pp, R, Tier, TIER_COLOR } from "@/lib/theme";
import { SlideProps } from "./types";

/* ------------------------------------------------------------------ 16. Final score */
export function FinalScore({ step }: SlideProps) {
  const M = R.bert_main.main;
  const win = R.bert_main.situation.find((s) => s.effect.startsWith("Won"))!;
  const rows = [
    { label: "Status and team focus", big: pp(M.all_controls.diff), col: C.gold,
      detail: <>points, superstar minus role player [{pp(M.all_controls.lo)}, {pp(M.all_controls.hi)}]; same player {pp(M.same_player.diff)}; gaps beyond about 4.5 ruled out.</> },
    { label: "Situation and team focus", big: `${pp(win.diff)}`, col: C.cream,
      detail: <>points of team-focused share after a win than after a loss; reporters&apos; wording and the round go with shifts too.</> },
    { label: "Status and words used", big: "differ", col: C.cream,
      detail: <>Superstars narrate the game, role players talk about being ready; words predict the tier, “I” and “we” add almost nothing.</> },
  ];
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Q4 · the answer" title="Final score" />
      {rows.map((r, k) => (
        <Reveal key={k} show={step >= k} x={-40} y={0} style={{ position: "absolute", left: 110, top: 284 + k * 160, width: 1700 }}>
          <Card style={{ height: 142, display: "flex", alignItems: "center", padding: "0 36px", gap: 36 }} glow={step === k ? C.gold : undefined}>
            <div className="font-cond" style={{ width: 420, fontSize: 30, fontWeight: 700, letterSpacing: "0.04em" }}>{r.label}</div>
            <div className="font-display" style={{ width: 260, fontSize: 104, lineHeight: 1, color: r.col, textAlign: "center",
              textShadow: r.col === C.gold ? "0 0 26px rgba(245,184,61,0.5)" : undefined }}>{r.big}</div>
            <div style={{ flex: 1, fontSize: 27, color: C.muted, lineHeight: 1.35 }}>{r.detail}</div>
          </Card>
        </Reveal>
      ))}
      <Reveal show={step >= 3} y={30} style={{ position: "absolute", left: 110, top: 776, width: 1700 }}>
        <div style={{ borderRadius: 22, padding: "26px 40px", background: "linear-gradient(100deg, rgba(245,184,61,0.2), rgba(28,21,16,0.85))",
          border: `2px solid ${C.gold}` }}>
          <div className="font-cond" style={{ fontSize: 22, letterSpacing: "0.2em", color: C.gold, fontWeight: 700 }}>TAKEAWAY</div>
          <div style={{ fontSize: 36, fontWeight: 600, lineHeight: 1.3, marginTop: 6 }}>
            Read in context, superstars and role players are about equally team-focused when they say “I” and “we”.
            Winning, losing and the questions asked go with bigger differences.
          </div>
        </div>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 17. Limits and next steps */
const LIMITS = [
  ["The training labels are AI-made", `human check (${R.human_check.n} random): “I” ${R.human_check.i.pct}%, κ = ${R.human_check.i.kappa.toFixed(2)} · misses about half of credit-giving “I” · picked after a first analysis`],
  ["Pronouns are one view of self-focus", "teammate credit differs between players, not within a player"],
  ["Observational, playoffs only", "consistent with, not proof · media training could flatten everyone"],
  ["Small gaps are still possible", "gaps beyond about 4.5 points are ruled out, smaller ones are not"],
];
const NEXT = [
  ["Human training labels", "two human coders, then retrain the classifier"],
  ["Coaches after wins and losses", "they speak for the team by role"],
  ["Beyond the NBA playoffs", "regular season, other sports"],
];

export function Limits({ step }: SlideProps) {
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Q4 · discussion" title="What this can't say, and what's next" />
      <div style={{ position: "absolute", left: 110, top: 300, width: 980 }}>
        <div className="font-cond" style={{ fontSize: 26, letterSpacing: "0.2em", color: C.gold, fontWeight: 700, marginBottom: 14 }}>LIMITS</div>
        {LIMITS.map(([h, d], k) => (
          <Reveal key={k} delay={0.25 + k * 0.12} x={-30} y={0}>
            <div style={{ display: "flex", gap: 20, marginBottom: 30, alignItems: "flex-start" }}>
              <span className="font-display" style={{ fontSize: 44, lineHeight: 1, color: C.gold, width: 40, flex: "none" }}>{k + 1}</span>
              <div>
                <div style={{ fontSize: 34, fontWeight: 700, lineHeight: 1.2 }}>{h}</div>
                <div style={{ fontSize: 25, color: C.muted, marginTop: 4 }}>{d}</div>
              </div>
            </div>
          </Reveal>
        ))}
      </div>
      <Reveal show={step >= 1} style={{ position: "absolute", left: 1150, top: 300, width: 660 }}>
        <Card style={{ padding: "28px 34px", height: 520 }} glow={C.gold}>
          <div className="font-cond" style={{ fontSize: 26, letterSpacing: "0.2em", color: C.gold, fontWeight: 700, marginBottom: 18 }}>NEXT</div>
          {NEXT.map(([h, d], k) => (
            <Reveal key={k} show={step >= 1} delay={0.2 + k * 0.15} x={20} y={0}>
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 30, fontWeight: 700 }}>→ {h}</div>
                <div style={{ fontSize: 24, color: C.muted, marginLeft: 34 }}>{d}</div>
              </div>
            </Reveal>
          ))}
          <div style={{ fontSize: 25, color: C.muted, lineHeight: 1.4, borderTop: "1px solid rgba(246,239,228,0.15)", paddingTop: 20 }}>
            <b style={{ color: C.cream }}>Why no lab effect?</b> An idea to test: at the podium, status is set against reporters, not teammates.
          </div>
        </Card>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 19. Fun fact: most and least team-focused players */
const FF = R.fun_fact;
const FX = lin(0.3, 0.9, 150, 1770);           // share -> stage x
const AXIS_Y = 450;
const DOT = 9;
/** Dots stacked upwards where they would overlap (a simple beeswarm), in share order. */
const SWARM = (() => {
  const placed: { x: number; row: number }[] = [];
  return [...FF.players].sort((p, q) => p.share - q.share).map((p) => {
    const x = FX(p.share);
    let row = 0;
    while (placed.some((d) => d.row === row && Math.abs(d.x - x) < 2 * DOT + 3)) row += 1;
    placed.push({ x, row });
    return { ...p, x, y: AXIS_Y - 22 - row * (2 * DOT + 3) };
  });
})();

function Extreme({ title, p, next, show }: { title: string; p: (typeof FF.players)[number]; next: (typeof FF.players)[number][]; show: boolean }) {
  const tier = (p.tiers.includes("/") ? null : p.tiers) as Tier | null;
  return (
    <Card style={{ height: 330, padding: "30px 36px", display: "flex", flexDirection: "column" }} glow={show ? C.gold : undefined}>
      <div className="font-cond" style={{ fontSize: 24, letterSpacing: "0.2em", color: C.gold, fontWeight: 700 }}>{title}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 34, marginTop: 18 }}>
        <Headshot id={p.id} size={170} ring={tier ? TIER_COLOR[tier] : C.gold} />
        <div>
          <div style={{ fontSize: 46, fontWeight: 700, lineHeight: 1.1 }}>{p.person}</div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 18, marginTop: 6 }}>
            <span className="font-display" style={{ fontSize: 100, lineHeight: 1, color: C.gold }}>{pct(p.share, 0)}%</span>
            {tier && <TierPill tier={tier} size={20} />}
          </div>
          <div style={{ fontSize: 22, color: C.muted, marginTop: 6 }}>{p.units} press conferences</div>
        </div>
      </div>
      <div style={{ fontSize: 24, color: C.muted, marginTop: "auto" }}>
        Next: {next.map((q) => `${q.person} ${pct(q.share, 0)}%`).join(" · ")}
      </div>
    </Card>
  );
}

export function FunFact({ step }: SlideProps) {
  const { active, bind } = usePick<number>();
  const top = FF.players.slice(0, 3);
  const bottom = FF.players.slice(-3).reverse();
  const lebron = SWARM.find((p) => p.person === "LeBron James")!;
  const gap = R.bert_main.main.all_controls.diff;
  const lit = (p: { person: string }) => (step >= 1 && p.person === top[0].person) || (step >= 2 && p.person === bottom[0].person);
  const hov = active === null ? null : SWARM[active];
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Fun fact · team-focused share per player" title="Most and least team-focused at the podium" size={80} />
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
        <line x1={FX(0.3)} x2={FX(0.9)} y1={AXIS_Y} y2={AXIS_Y} stroke={C.grid} strokeWidth={2} />
        {[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9].map((v) => (
          <g key={v}>
            <line x1={FX(v)} x2={FX(v)} y1={AXIS_Y} y2={AXIS_Y + 8} stroke={C.grid} strokeWidth={2} />
            <text x={FX(v)} y={AXIS_Y + 34} textAnchor="middle" fontSize={22} fill={C.dim}>{v * 100}%</text>
          </g>
        ))}
        <line x1={FX(FF.median)} x2={FX(FF.median)} y1={AXIS_Y - 12} y2={AXIS_Y + 52} stroke={C.muted} strokeWidth={2} strokeDasharray="5 6" />
        <text x={FX(FF.median) + 10} y={AXIS_Y + 64} fontSize={21} fill={C.muted}>median {pct(FF.median, 0)}%</text>
      </svg>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {SWARM.map((p, k) => (
          <motion.circle key={p.person} cx={p.x} cy={p.y} r={lit(p) || active === k ? DOT + 3 : DOT}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 + k * 0.012 }}
            fill={lit(p) ? C.gold : p === lebron ? C.cream : a(C.muted, 0.6)} stroke={C.bg} strokeWidth={2}
            className="tap" {...bind(k)} />
        ))}
      </svg>
      <div style={{ position: "absolute", left: lebron.x - 60, top: AXIS_Y + 44, fontSize: 21, color: C.cream, pointerEvents: "none" }}>
        ↑ LeBron {pct(lebron.share, 0)}%
      </div>
      <Tip show={hov !== null} x={hov ? hov.x : 0} y={hov ? hov.y - 18 : 0}
        anchor={!hov ? "above" : hov.x > 1250 ? "above-right" : hov.x < 650 ? "above-left" : "above"}>
        {hov && <><b>{hov.person}</b> · {pct(hov.share, 1)}% · {hov.units} press conferences · {hov.pron.toLocaleString()} pronouns</>}
      </Tip>
      <Reveal show={step >= 2} delay={0.5} style={{ position: "absolute", left: 1290, top: 300, width: 520, textAlign: "right" }}>
        <div style={{ fontSize: 23, color: C.muted }}>
          players span {Math.round((FF.players[0].share - FF.players[FF.players.length - 1].share) * 100)} points;
          {" "}superstar − role: <b style={{ color: C.gold }}>{pp(gap)}</b>
        </div>
      </Reveal>

      <Reveal show={step >= 1} style={{ position: "absolute", left: 110, top: 555, width: 830 }}>
        <Extreme title="MOST TEAM-FOCUSED" p={top[0]} next={top.slice(1)} show={step === 1} />
      </Reveal>
      <Reveal show={step >= 2} style={{ position: "absolute", left: 980, top: 555, width: 830 }}>
        <Extreme title="LEAST TEAM-FOCUSED" p={bottom[0]} next={bottom.slice(1)} show={step === 2} />
      </Reveal>
      <Reveal show={step >= 2} delay={0.4} style={{ position: "absolute", left: 110, top: 918, width: 1700 }}>
        <div style={{ fontSize: 22, color: C.dim, lineHeight: 1.4 }}>
          {FF.n_players} players with ≥ {FF.min_pron} self + team pronouns and ≥ {FF.min_units} press conferences · pooled, no controls ·
          {" "}with the six controls {top[0].person.split(" ")[1]} ranks {top[0].adj_rank}th, same bottom three
        </div>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 18. Thanks, references and credits */
const REFS = [
  "Cialdini, R. B., et al. (1976). Basking in reflected glory: Three (football) field studies. JPSP, 34(3), 366–375.",
  "Kacewicz, E., Pennebaker, J. W., Davis, M., Jeon, M., & Graesser, A. C. (2014). Pronoun use reflects standings in social hierarchies. JLSP, 33(2), 125–143.",
  "Monroe, B. L., Colaresi, M. P., & Quinn, K. M. (2008). Fightin' words: Lexical feature selection and evaluation for identifying the content of political conflict. Political Analysis, 16(4), 372–403.",
  "Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent Dirichlet allocation. JMLR, 3, 993–1022.",
  "Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. NAACL-HLT 2019, 4171–4186.",
];
const DATA = [
  "Transcripts: ASAP Sports (asapsports.com), scraped for this project",
  "Games and starts: stats.nba.com via nba_api · All-Star and All-NBA lists: Wikipedia",
  "Tools: Python (pandas, statsmodels, scikit-learn, sentence-transformers MiniLM, transformers bert-base-uncased); slides: Next.js + Framer Motion",
  "Photos: player headshots, NBA.com · “Pacers Paul George” and “Dwight Howard Press Conference” by All-Pro Reels, CC BY-SA 2.0 · NBA All-Star announcement press conference, Indianapolis Mayor's Office, public domain (Wikimedia Commons)",
];

export function Credits() {
  const [bounces, setBounces] = useState(0); // click the ball to bounce it again
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <div style={{ position: "absolute", left: 110, top: 130, width: 1700 }}>
        <Kicker>Final buzzer</Kicker>
        <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
          <Title text="Thank you" size={150} />
          <motion.div key={bounces} className="tap" onClick={stop(() => setBounces((n) => n + 1))}
            initial={{ y: -300, opacity: bounces ? 1 : 0 }} animate={{ y: [-300, 0, -90, 0, -30, 0], opacity: 1 }}
            transition={{ duration: 1.6, times: [0, 0.35, 0.55, 0.72, 0.86, 1], ease: "easeIn", delay: bounces ? 0 : 0.4 }}>
            <Ball size={110} />
          </motion.div>
        </div>
      </div>
      <Reveal delay={0.6} style={{ position: "absolute", left: 110, top: 400, width: 1700, display: "flex", gap: 60 }}>
        <div style={{ flex: 1 }}>
          <div className="font-cond" style={{ fontSize: 24, letterSpacing: "0.2em", color: C.gold, fontWeight: 700, marginBottom: 12 }}>REFERENCES</div>
          {REFS.map((r) => <p key={r} style={{ fontSize: 22, color: C.muted, lineHeight: 1.4, margin: "0 0 12px" }}>{r}</p>)}
        </div>
        <div style={{ flex: 1 }}>
          <div className="font-cond" style={{ fontSize: 24, letterSpacing: "0.2em", color: C.gold, fontWeight: 700, marginBottom: 12 }}>DATA, TOOLS AND CREDITS</div>
          {DATA.map((r) => <p key={r} style={{ fontSize: 22, color: C.muted, lineHeight: 1.4, margin: "0 0 12px" }}>{r}</p>)}
        </div>
      </Reveal>
    </div>
  );
}
