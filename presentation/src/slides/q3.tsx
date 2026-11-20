"use client";

import { motion } from "framer-motion";
import { ReactNode, useState } from "react";
import { Ball, Card, CountUp, Header, Legend, Reveal, stop, Tip, usePick } from "@/components/ui";
import { a, C, ease, lin, pct, pp, R, Tier, TIER_COLOR, TIER_NAME, TIERS } from "@/lib/theme";
import { SlideProps } from "./types";

const ciTxt = (lo: number, hi: number) => `[${pp(lo)}, ${pp(hi)}]`;

/* ------------------------------------------------------------------ 10. Main result */
export function MainResult({ step }: SlideProps) {
  const M = R.bert_main.main;
  const SD = R.bert_main.sd;
  const groups = [
    { key: "no_controls" as const, label: "No controls" },
    { key: "all_controls" as const, label: "All controls" },
    { key: "same_player" as const, label: "Same player" },
  ];
  const Y = lin(0.55, 0.72, 850, 330);
  const GX = (g: number) => 1000 + g * 280;
  const off: Record<Tier, number> = { role: -62, starter: 0, superstar: 62 };
  const NX = lin(-0.1, 0.1, 170, 670);
  const [sel, setSel] = useState<(typeof groups)[number]["key"] | null>(null); // click a model name to show it on the scoreboard
  const shown = sel ?? "all_controls";
  const pick = usePick<number>(); // hover a column for the numbers
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Q3 · main result" title="The team-focused share is about the same in every tier" size={80} />
      {/* scoreboard */}
      <Reveal delay={0.3} style={{ position: "absolute", left: 110, top: 300, width: 650 }}>
        <div style={{ background: "radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1.6px) 0 0 / 7px 7px, linear-gradient(#141312, #070606)",
          border: "2px solid #3d3a36", borderRadius: 16,
          padding: "20px 24px 26px", boxShadow: "0 16px 40px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.07), inset 0 0 30px rgba(0,0,0,0.7)" }}>
          <div className="font-cond" style={{ fontSize: 22, letterSpacing: "0.18em", color: C.gold, fontWeight: 700, textAlign: "center" }}>
            TEAM-FOCUSED SHARE, {groups.find((g) => g.key === shown)!.label.toUpperCase()} (%)
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 14 }}>
            {TIERS.map((t, k) => (
              <div key={t} style={{ textAlign: "center", flex: 1 }}>
                <div className="font-cond" style={{ fontSize: 22, fontWeight: 700, letterSpacing: "0.1em", color: TIER_COLOR[t] }}>{TIER_NAME[t].toUpperCase()}</div>
                <div className="font-display" style={{ fontSize: 104, lineHeight: 1, color: C.led, textShadow: "0 0 18px rgba(255,181,71,0.55)" }}>
                  <CountUp key={shown} to={M[shown].tiers[t].est * 100} decimals={1} delay={sel ? k * 0.08 : 0.5 + k * 0.15} duration={sel ? 0.8 : 1.5} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </Reveal>
      {/* gap on a number line */}
      <Reveal show={step >= 2} style={{ position: "absolute", left: 110, top: 600, width: 650 }}>
        <Card style={{ padding: "22px 26px", height: 370 }}>
          <div className="font-cond" style={{ fontSize: 22, letterSpacing: "0.14em", color: C.gold, fontWeight: 700 }}>SUPERSTAR MINUS ROLE PLAYER (POINTS)</div>
          <svg width="600" height="250" style={{ marginTop: 8 }}>
            {step >= 3 && (
              <>
                <motion.rect x={NX(-0.1) - 110} y={20} width={NX(M.all_controls.lo) - NX(-0.1)} height={150} fill="rgba(246,239,228,0.08)"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} />
                <motion.rect x={NX(M.all_controls.hi) - 110} y={20} width={NX(0.1) - NX(M.all_controls.hi)} height={150} fill="rgba(246,239,228,0.08)"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} />
                <text x={(NX(-0.1) + NX(M.all_controls.lo)) / 2 - 110} y={44} textAnchor="middle" fontSize={18} fill={C.muted}>ruled out</text>
                <text x={(NX(M.all_controls.hi) + NX(0.1)) / 2 - 110} y={44} textAnchor="middle" fontSize={18} fill={C.muted}>ruled out</text>
              </>
            )}
            <line x1={NX(0) - 110} x2={NX(0) - 110} y1={20} y2={170} stroke={C.cream} strokeOpacity={0.5} strokeWidth={2} />
            {[{ d: M.all_controls, y: 80, label: "All controls", main: true }, { d: M.same_player, y: 135, label: "Same player", main: false }].map((r) => (
              <g key={r.label}>
                <motion.line y1={r.y} y2={r.y} stroke={TIER_COLOR.superstar} strokeWidth={r.main ? 8 : 5} strokeLinecap="round"
                  initial={{ x1: NX(0) - 110, x2: NX(0) - 110 }} animate={step >= 2 ? { x1: NX(r.d.lo) - 110, x2: NX(r.d.hi) - 110 } : {}}
                  transition={{ duration: 0.8, delay: 0.3, ease }} strokeOpacity={r.main ? 1 : 0.6} />
                <motion.circle cy={r.y} r={r.main ? 12 : 9} fill={TIER_COLOR.superstar} stroke={C.surface} strokeWidth={3}
                  initial={{ cx: NX(0) - 110 }} animate={{ cx: NX(r.d.diff) - 110 }} transition={{ duration: 0.8, delay: 0.3 }} />
                <text x={NX(r.d.lo) - 110} y={r.y - 16} fontSize={18} fill={C.muted}>{r.label}</text>
              </g>
            ))}
            {[-0.1, -0.05, 0, 0.05, 0.1].map((v) => (
              <text key={v} x={NX(v) - 110} y={200} textAnchor="middle" fontSize={20} fill={C.muted}>{v === 0 ? "0" : pp(v, 0)}</text>
            ))}
          </svg>
          <div style={{ fontSize: 25, lineHeight: 1.3, marginTop: -4 }}>
            <b style={{ color: C.cream }}>{pp(M.all_controls.diff)} points</b> {ciTxt(M.all_controls.lo, M.all_controls.hi)}
            <span style={{ color: C.muted }}> · same player {pp(M.same_player.diff)} {ciTxt(M.same_player.lo, M.same_player.hi)}</span>
          </div>
        </Card>
      </Reveal>
      {/* CI chart */}
      <Reveal show={step >= 1} y={0} style={{ position: "absolute", left: 820, top: 290 }}>
        <svg width="1000" height="700">
          <g transform="translate(-820,-290)">
            {[0.6, 0.65, 0.7].map((v) => (
              <g key={v}>
                <line x1={900} x2={1800} y1={Y(v)} y2={Y(v)} stroke={C.grid} strokeWidth={v === 0.5 ? 2 : 1.5} strokeDasharray={v === 0.5 ? "8 8" : undefined} />
                <text x={890} y={Y(v) + 7} textAnchor="end" fontSize={22} fill={C.muted}>{pct(v, 0)}%</text>
              </g>
            ))}
            {groups.map((g, gi) => (
              <motion.g key={g.key} animate={{ opacity: sel && sel !== g.key ? 0.3 : 1 }}>
                <g className="tap" onClick={stop(() => setSel(sel === g.key ? null : g.key))}>
                  <rect x={GX(gi) - 100} y={872} width={200} height={42} rx={21}
                    fill={sel === g.key ? "rgba(245,184,61,0.2)" : "rgba(246,239,228,0.05)"}
                    stroke={sel === g.key ? C.gold : "rgba(246,239,228,0.28)"} strokeWidth={2} />
                  <text x={GX(gi)} y={901} textAnchor="middle" fontSize={25} fontWeight={600} fill={C.cream}>{g.label}</text>
                </g>
                {TIERS.map((t, ti) => {
                  const d = M[g.key].tiers[t];
                  const x = GX(gi) + off[t];
                  const dl = 0.2 + gi * 0.35 + ti * 0.1;
                  return (
                    <g key={t}>
                      <motion.line x1={x} x2={x} stroke={TIER_COLOR[t]} strokeWidth={6} strokeLinecap="round"
                        initial={{ y1: Y(d.est), y2: Y(d.est) }} animate={step >= 1 ? { y1: Y(d.lo), y2: Y(d.hi) } : {}}
                        transition={{ delay: dl + 0.4, duration: 0.6 }} />
                      <motion.circle cx={x} r={14} fill={TIER_COLOR[t]} stroke={C.floor} strokeWidth={4}
                        initial={{ cy: 280, opacity: 0 }} animate={step >= 1 ? { cy: Y(d.est), opacity: 1 } : {}}
                        transition={{ delay: dl, type: "spring", stiffness: 120, damping: 11 }} />
                    </g>
                  );
                })}
                <rect x={GX(gi) - 110} y={300} width={220} height={560} fill="transparent" {...pick.hover(gi)} />
              </motion.g>
            ))}
          </g>
        </svg>
        {groups.map((g, gi) => (
          <Tip key={g.key} show={pick.active === gi} x={gi < 2 ? GX(gi) - 820 + 92 : GX(gi) - 820 - 92} y={110} anchor={gi < 2 ? "left" : "right"}>
            <div className="font-cond" style={{ fontSize: 19, letterSpacing: "0.14em", color: C.gold, fontWeight: 700 }}>{g.label.toUpperCase()}</div>
            {TIERS.map((t) => {
              const d = M[g.key].tiers[t];
              return (
                <div key={t} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ width: 14, height: 14, borderRadius: "50%", background: TIER_COLOR[t] }} />
                  {TIER_NAME[t]} <b>{pct(d.est)}%</b> <span style={{ color: C.muted }}>[{pct(d.lo)}, {pct(d.hi)}]</span>
                </div>
              );
            })}
            <div style={{ fontSize: 18, color: C.muted, marginTop: 4 }}>
              Superstar − role {pp(M[g.key].diff)} [{pp(M[g.key].lo)}, {pp(M[g.key].hi)}] · {M[g.key].n_players} players
            </div>
          </Tip>
        ))}
        <Legend style={{ position: "absolute", left: 90, top: -6 }} items={TIERS.map((t) => ({ label: TIER_NAME[t], color: TIER_COLOR[t] }))} />
      </Reveal>
      <Reveal show={step >= 3} delay={0.3} style={{ position: "absolute", left: 830, top: 932, width: 980 }}>
        <div style={{ fontSize: 21, color: C.muted, textAlign: "center" }}>
          Adjusted predictions · 95% CI (delta method) · gaps beyond {pp(M.all_controls.lo)} / {pp(M.all_controls.hi)} pp (≈{(Math.max(-M.all_controls.lo, M.all_controls.hi) / SD).toFixed(1)} SD) ruled out
        </div>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 11. Situation */
const SIT_LABEL: Record<string, string> = {
  "Won vs lost (game days)": "After a win (vs a loss)",
  "Conference finals vs NBA Finals": "Conference finals (vs NBA Finals)",
  "+10 'you' per 1,000 question words": "+10 “you” per 1,000 question words",
  "+10 points scored (game days)": "Scored 10 more points",
  "Superstar vs role player": "Superstar (vs role player)",
};

export function Situation({ step }: SlideProps) {
  const rows = [...R.bert_main.situation].sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff));
  const pick = usePick<number>(); // hover a row for its 95% CI
  const X = lin(-0.13, 0.09, 640, 1240);
  const fans = { win: 32, loss: 18 };
  const players = { win: R.bert_main.raw_gameday.won * 100, loss: R.bert_main.raw_gameday.lost * 100 };
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Q3 · what goes with it" title="Winning and losing go with bigger shifts than status" size={80} />
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0 }}>
        {[-0.12, -0.08, -0.04, 0, 0.04, 0.08].map((v) => (
          <g key={v}>
            <line x1={X(v)} x2={X(v)} y1={320} y2={860} stroke={v === 0 ? C.cream : C.grid} strokeOpacity={v === 0 ? 0.6 : 1} strokeWidth={v === 0 ? 2.5 : 1.5} />
            <text x={X(v)} y={895} textAnchor="middle" fontSize={22} fill={C.muted}>{v === 0 ? "0" : pp(v, 0)}</text>
          </g>
        ))}
        <text x={X(0)} y={935} textAnchor="middle" fontSize={22} fill={C.muted}>average marginal effect on the team-focused share (pp)</text>
        {rows.map((r, k) => {
          const y = 360 + k * 108;
          const isStatus = r.effect.startsWith("Superstar");
          const col = isStatus ? TIER_COLOR.superstar : C.muted;
          const focus = step === 1 ? isStatus : step === 2 ? r.effect.startsWith("Won") : true;
          const dim = focus ? 1 : 0.3;
          return (
            <motion.g key={r.effect} animate={{ opacity: dim }} transition={{ duration: 0.4 }}>
              <text x={600} y={y + 9} textAnchor="end" fontSize={27} fontWeight={isStatus ? 700 : 500} fill={C.cream}>{SIT_LABEL[r.effect]}</text>
              <motion.rect y={y - 20} height={40} rx={6} fill={col}
                initial={{ x: X(0), width: 0 }} animate={{ x: Math.min(X(0), X(r.diff)), width: Math.abs(X(r.diff) - X(0)) }}
                transition={{ delay: 0.4 + k * 0.15, duration: 0.8, ease }} />
              <motion.line y1={y} y2={y} x1={X(r.lo)} x2={X(r.hi)} stroke={C.cream} strokeWidth={3}
                initial={{ opacity: 0 }} animate={{ opacity: 0.9 }} transition={{ delay: 1.2 + k * 0.15 }} />
              <motion.text x={1268} y={y + 9} textAnchor="start"
                fontSize={28} fontWeight={700} fill={isStatus ? TIER_COLOR.superstar : C.cream}
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.3 + k * 0.15 }}>
                {pp(r.diff)}
              </motion.text>
              <rect x={250} y={y - 50} width={1080} height={100} fill="transparent" {...pick.hover(k)} />
            </motion.g>
          );
        })}
      </svg>
      {rows.map((r, k) => (
        <Tip key={r.effect} show={pick.active === k} x={X(0)} y={360 + k * 108 - 30} anchor="above">
          {SIT_LABEL[r.effect]}: <b>{pp(r.diff)} points</b> of team-focused share <span style={{ color: C.muted }}>95% CI [{pp(r.lo)}, {pp(r.hi)}]</span>
        </Tip>
      ))}
      <Reveal show={step === 1} delay={0.2} x={0} y={-10} style={{ position: "absolute", left: 975, top: 818, width: 340 }}>
        <div style={{ fontSize: 24, color: TIER_COLOR.superstar, fontWeight: 700, lineHeight: 1.2 }}>↑ status: the smallest shift</div>
      </Reveal>
      <Reveal show={step >= 2} style={{ position: "absolute", left: 1340, top: 300, width: 470 }}>
        <Card style={{ padding: "26px 30px", height: 640 }} glow={C.gold}>
          <div className="font-display" style={{ fontSize: 52, lineHeight: 1 }}>Players are the opposite of fans</div>
          <svg width="410" height="345" style={{ marginTop: 14 }}>
            {[{ g: "Fans", sub: "Cialdini et al. (1976)", d: fans, x: 30 }, { g: "Players", sub: "this data, game days", d: players, x: 230 }].map((b, j) => (
              <g key={b.g}>
                {(["win", "loss"] as const).map((w, k) => {
                  const h = (b.d[w] / 80) * 220;
                  return (
                    <g key={w}>
                      <motion.rect x={b.x + k * 78} width={64} rx={6} fill={w === "win" ? C.gold : C.dim}
                        initial={{ y: 250, height: 0 }} animate={step >= 2 ? { y: 250 - h, height: h } : {}}
                        transition={{ delay: 0.4 + j * 0.3 + k * 0.1, duration: 0.7, ease }} />
                      <text x={b.x + k * 78 + 32} y={240 - h} textAnchor="middle" fontSize={22} fontWeight={700} fill={C.cream}>{Math.round(b.d[w])}%</text>
                      <text x={b.x + k * 78 + 32} y={276} textAnchor="middle" fontSize={20} fill={C.muted}>{w === "win" ? "win" : "loss"}</text>
                    </g>
                  );
                })}
                <text x={b.x + 71} y={310} textAnchor="middle" fontSize={24} fontWeight={700} fill={C.cream}>{b.g}</text>
                <text x={b.x + 71} y={330} textAnchor="middle" fontSize={16} fill={C.muted}>{b.sub}</text>
              </g>
            ))}
          </svg>
          <p style={{ fontSize: 22, color: C.muted, lineHeight: 1.35, margin: "12px 0 0" }}>
            Fans: descriptions that used “we”. Players: team-focused share. Different measures, opposite direction.
          </p>
        </Card>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 12. Fightin' Words */
const GAME = new Set(["tonight", "quarter", "made", "missed", "aggressive", "better", "didn't", "thought"]);
const READY = new Set(["ready", "here"]); // the role-side words that also hold one player at a time

export function Words({ step }: SlideProps) {
  const sup = R.words.superstar, rol = R.words.role;
  const L = (z: number) => (Math.abs(z) / 12) * 560;
  const pick = usePick<string>(); // hover a word for its score
  const tipFor = (w: { word: string; z: number; holds: boolean }, side: "s" | "r", k: number) => (
    <Tip key={side + w.word} show={pick.active === side + w.word} x={side === "s" ? 975 + L(w.z) + 16 : 945 - L(w.z) - 16}
      y={355 + k * 51 - 2} anchor={side === "s" ? "left" : "right"} accent={side === "s" ? TIER_COLOR.superstar : TIER_COLOR.role}>
      <b>{w.word === "i" ? "I" : w.word}</b> · z = {Math.abs(w.z).toFixed(1)} ·{" "}
      <span style={{ color: C.muted }}>{w.holds ? "holds at player level" : "pooled only"}</span>
    </Tip>
  );
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Q3 · what does differ · Fightin' Words (Monroe et al., 2008): log-odds, informative Dirichlet prior" title="They differ in what they talk about" />
      <div className="font-cond" style={{ position: "absolute", left: 110, top: 292, width: 830, textAlign: "right", fontSize: 26, fontWeight: 700, letterSpacing: "0.1em", color: TIER_COLOR.role }}>
        ← ROLE PLAYERS USE MORE
      </div>
      <div className="font-cond" style={{ position: "absolute", left: 980, top: 292, fontSize: 26, fontWeight: 700, letterSpacing: "0.1em", color: TIER_COLOR.superstar }}>
        SUPERSTARS USE MORE →
      </div>
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0 }}>
        <line x1={960} x2={960} y1={335} y2={860} stroke={C.cream} strokeOpacity={0.4} strokeWidth={2} />
        {sup.map((w, k) => {
          const y = 355 + k * 51;
          const hi = step !== 1 || GAME.has(w.word);
          const isI = w.word === "i";
          return (
            <motion.g key={w.word} animate={{ opacity: hi ? 1 : 0.28 }}>
              <motion.rect x={975} y={y} height={40} rx={6} fill={w.holds ? TIER_COLOR.superstar : "transparent"}
                stroke={TIER_COLOR.superstar} strokeWidth={3} initial={{ width: 0 }} animate={{ width: L(w.z) }}
                transition={{ delay: 0.3 + k * 0.06, duration: 0.7, ease }} />
              <text x={990} y={y + 29} fontSize={26} fontWeight={700} fill="#fff">{isI ? "I (the pronoun)" : w.word}</text>
              <rect x={962} y={y - 4} width={620} height={48} fill="transparent" {...pick.hover("s" + w.word)} />
            </motion.g>
          );
        })}
        {rol.map((w, k) => {
          const y = 355 + k * 51;
          const hi = step !== 1 || READY.has(w.word);
          return (
            <motion.g key={w.word} animate={{ opacity: hi ? 1 : 0.28 }}>
              <motion.rect y={y} height={40} rx={6} fill={w.holds ? TIER_COLOR.role : "transparent"} stroke={TIER_COLOR.role} strokeWidth={3}
                initial={{ x: 945, width: 0 }} animate={{ x: 945 - L(w.z), width: L(w.z) }}
                transition={{ delay: 0.3 + k * 0.06, duration: 0.7, ease }} />
              <text x={930} y={y + 29} textAnchor="end" fontSize={26} fontWeight={700} fill="#fff">{w.word}</text>
              <rect x={338} y={y - 4} width={620} height={48} fill="transparent" {...pick.hover("r" + w.word)} />
            </motion.g>
          );
        })}
      </svg>
      {sup.map((w, k) => tipFor(w, "s", k))}
      {rol.map((w, k) => tipFor(w, "r", k))}
      <Reveal show={step >= 1} delay={0.2} x={20} y={0} style={{ position: "absolute", left: 1590, top: 400, width: 230 }}>
        <div className="font-display" style={{ fontSize: 52, lineHeight: 1, color: TIER_COLOR.superstar }}>narrating the game</div>
      </Reveal>
      <Reveal show={step >= 1} delay={0.3} x={-20} y={0} style={{ position: "absolute", left: 110, top: 400, width: 240 }}>
        <div className="font-display" style={{ fontSize: 52, lineHeight: 1, color: TIER_COLOR.role }}>being ready</div>
      </Reveal>
      <Legend style={{ position: "absolute", left: 560, top: 880 }} items={[
        { label: "holds at player level (Mann–Whitney)", color: C.cream },
        { label: "pooled only", color: C.cream, hollow: true },
      ]} />
      <Reveal show={step >= 2} style={{ position: "absolute", left: 110, top: 930, width: 1700 }}>
        <div style={{ fontSize: 27, textAlign: "center" }}>
          Superstars use more of <b>both</b>: <span style={{ color: C.i, fontWeight: 700 }}>“I” {R.words.families.i.superstar} vs {R.words.families.i.role}</span> and{" "}
          <span style={{ color: C.we, fontWeight: 700 }}>“we” {R.words.families.we.superstar} vs {R.words.families.we.role}</span> per 1,000 words, so the share stays flat.
        </div>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 13. Classifiers */
const CLS = [
  { k: "E1" as const, label: "“I” and “we” rates only" },
  { k: "E3" as const, label: "Sentence embeddings (MiniLM)" },
  { k: "B1" as const, label: "Session and round only (no words)" },
  { k: "B2" as const, label: "Answer length only (no words)" },
  { k: "E2b" as const, label: "All words except “I” and “we”" },
  { k: "E2" as const, label: "All words" },
];

export function Classifiers({ step }: SlideProps) {
  const X = lin(0.45, 0.9, 760, 1700);
  const pick = usePick<number>(); // hover a row for its 95% CI
  const [rolls, setRolls] = useState(CLS.map(() => 0)); // click a ball to roll it again
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Q3 · can a model tell them apart? · logistic regression classifiers" title="Words predict the tier; “I” and “we” add almost nothing" size={80} />
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0 }}>
        {[0.5, 0.6, 0.7, 0.8, 0.9].map((v) => (
          <g key={v}>
            <line x1={X(v)} x2={X(v)} y1={320} y2={880} stroke={v === 0.5 ? C.cream : C.grid} strokeOpacity={v === 0.5 ? 0.55 : 1}
              strokeWidth={v === 0.5 ? 2.5 : 1.5} strokeDasharray={v === 0.5 ? "8 8" : undefined} />
            <text x={X(v)} y={915} textAnchor="middle" fontSize={22} fill={C.muted}>{v.toFixed(1)}</text>
          </g>
        ))}
        <text x={X(0.5) + 10} y={312} fontSize={22} fill={C.muted}>chance</text>
        {CLS.map((c, k) => {
          const d = R.classifiers[c.k];
          const y = 370 + k * 98;
          const focus = step === 1 ? c.k === "E1" : step >= 2 ? c.k === "E2" || c.k === "E2b" : true;
          return (
            <motion.g key={c.k} animate={{ opacity: focus ? 1 : 0.3 }}>
              <text x={720} y={y + 9} textAnchor="end" fontSize={27} fontWeight={600} fill={C.cream}>{c.label}</text>
              <motion.line y1={y} y2={y} x1={X(d.lo)} x2={X(d.hi)} stroke={C.gold} strokeOpacity={0.5} strokeWidth={6} strokeLinecap="round"
                initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 1.2 + k * 0.12 }} />
              <motion.text y={y + 9} fontSize={28} fontWeight={700} fill={C.cream} initial={{ opacity: 0, x: X(d.hi) + 14 }}
                animate={{ opacity: 1 }} transition={{ delay: 1.4 + k * 0.12 }}>{d.auc.toFixed(2)}</motion.text>
              <rect x={110} y={y - 46} width={1700} height={92} fill="transparent" {...pick.hover(k)} />
            </motion.g>
          );
        })}
      </svg>
      {CLS.map((c, k) => {
        const d = R.classifiers[c.k];
        const y = 370 + k * 98;
        const focus = step === 1 ? c.k === "E1" : step >= 2 ? c.k === "E2" || c.k === "E2b" : true;
        return (
          <motion.div key={`${c.k}${rolls[k]}`} style={{ position: "absolute", top: y - 20, zIndex: 5 }} className="tap"
            onClick={stop(() => setRolls((r) => r.map((v, j) => (j === k ? v + 1 : v))))}
            initial={{ left: X(0.45) - 20, rotate: 0, opacity: rolls[k] ? 1 : 0 }}
            animate={{ left: X(d.auc) - 20, rotate: (X(d.auc) - X(0.45)) * 1.2, opacity: focus ? 1 : 0.3 }}
            transition={{ left: { delay: rolls[k] ? 0 : 0.3 + k * 0.12, duration: 1.1, ease }, rotate: { delay: rolls[k] ? 0 : 0.3 + k * 0.12, duration: 1.1, ease }, opacity: { duration: 0.4 } }}>
            <Ball size={40} />
          </motion.div>
        );
      })}
      {CLS.map((c, k) => {
        const d = R.classifiers[c.k];
        return (
          <Tip key={c.k} show={pick.active === k} x={X(d.auc)} y={370 + k * 98 - 30} anchor="above">
            AUC <b>{d.auc.toFixed(3)}</b> <span style={{ color: C.muted }}>95% CI [{d.lo.toFixed(2)}, {d.hi.toFixed(2)}]</span>
          </Tip>
        );
      })}
      <Reveal show={step === 1} x={-20} y={0} style={{ position: "absolute", left: X(R.classifiers.E1.hi) + 90, top: 352 }}>
        <div style={{ fontSize: 26, fontWeight: 700, color: C.gold }}>← pronoun rates alone ≈ chance</div>
      </Reveal>
      <Reveal show={step >= 2} x={-20} y={0} style={{ position: "absolute", left: 1480, top: 628, width: 320 }}>
        <div style={{ fontSize: 26, fontWeight: 700, color: C.gold, lineHeight: 1.2 }}>same score with or without “I” and “we” ↓</div>
      </Reveal>
      <div style={{ position: "absolute", left: 110, top: 945, width: 1700, fontSize: 21, color: C.muted, textAlign: "center" }}>
        AUC, superstar vs role-player units · stratified group 5-fold CV (held-out players) · 95% CI: player bootstrap
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ 14. Topics */
/* ------------------------------------------------------------------ What reporters ask (Step 21): LDA topic gaps, raw vs same round and session */
const LT = R.lda_tiers;
const QX = lin(-0.07, 0.07, 640, 1260);   // superstar − role gap (share of question words) -> stage x
const QY = (k: number) => 372 + k * 54;

export function Questions({ step }: SlideProps) {
  const pick = usePick<number>();
  const hold = LT.topics.filter((t) => t.holds).map((t) => t.name);
  const ci = (g: { d: number; lo: number; hi: number }, y: number, col: string, k: number, delay: number) => (
    <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: delay + k * 0.05, duration: 0.4 }}>
      <line x1={QX(g.lo)} x2={QX(g.hi)} y1={y} y2={y} stroke={col} strokeWidth={3} strokeOpacity={0.8} />
      <circle cx={QX(g.d)} cy={y} r={9} fill={col} stroke={C.floor} strokeWidth={2} />
    </motion.g>
  );
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Q3 · what reporters ask · LDA topics of the questions (K = 10)" title="Question topics differ by tier, mostly through timing" size={80} />
      <div className="font-cond" style={{ position: "absolute", left: 640, top: 300, width: 300, fontSize: 21, fontWeight: 700, letterSpacing: "0.08em", color: TIER_COLOR.role }}>
        ← ASKED MORE OF ROLE PLAYERS
      </div>
      <div className="font-cond" style={{ position: "absolute", left: 960, top: 300, width: 300, textAlign: "right", fontSize: 21, fontWeight: 700, letterSpacing: "0.08em", color: TIER_COLOR.superstar }}>
        ASKED MORE OF SUPERSTARS →
      </div>
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0 }}>
        {[-0.06, -0.04, -0.02, 0, 0.02, 0.04, 0.06].map((v) => (
          <g key={v}>
            <line x1={QX(v)} x2={QX(v)} y1={345} y2={QY(9) + 26} stroke={v === 0 ? C.muted : C.grid} strokeWidth={v === 0 ? 2 : 1.5} />
            <text x={QX(v)} y={QY(9) + 58} textAnchor="middle" fontSize={21} fill={C.muted}>{v === 0 ? "0" : pp(v, 0)}</text>
          </g>
        ))}
        <text x={QX(0)} y={QY(9) + 90} textAnchor="middle" fontSize={21} fill={C.muted}>superstar − role player, points of question share · 95% CI, clustered by player</text>
        {LT.topics.map((t, k) => {
          const y = QY(k);
          const dim = step >= 2 && !t.holds;
          return (
            <motion.g key={t.topic} animate={{ opacity: dim ? 0.35 : 1 }}>
              <text x={610} y={y + 8} textAnchor="end" fontSize={25} fontWeight={step >= 2 && t.holds ? 700 : 500} fill={C.cream}>{t.name}</text>
              {ci(t.raw, step >= 1 ? y - 8 : y, C.muted, k, 0.3)}
              {step >= 1 && ci(t.adj, y + 8, C.gold, k, 0.1)}
              <rect x={150} y={y - 27} width={1120} height={54} fill="transparent" className="tap" {...pick.bind(k)} />
            </motion.g>
          );
        })}
      </svg>
      <Legend style={{ position: "absolute", left: 640, top: QY(9) + 104 }} items={[
        { label: "all units", color: C.muted }, ...(step >= 1 ? [{ label: "same round and game day", color: C.gold }] : [])]} />
      {LT.topics.map((t, k) => (
        <Tip key={t.topic} show={pick.active === k} x={1275} y={k < 5 ? QY(k) + 22 : QY(k) - 22} anchor={k < 5 ? "right" : "above-right"} width={620}>
          <b>{t.name}</b>: {t.words.join(", ")}
          <div style={{ fontSize: 19, color: C.muted, marginTop: 6 }}>
            share of questions: role {pct(t.mean.role)}% · starter {pct(t.mean.starter)}% · superstar {pct(t.mean.superstar)}%<br />
            gap {pp(t.raw.d)} {ciTxt(t.raw.lo, t.raw.hi)}; same round and game day {pp(t.adj.d)} {ciTxt(t.adj.lo, t.adj.hi)}
          </div>
        </Tip>
      ))}
      <Reveal delay={0.5} style={{ position: "absolute", left: 1330, top: 300, width: 480 }}>
        <Card style={{ overflow: "hidden", height: 660 }} glow={step === 1 ? C.gold : undefined}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/img/press/room.jpg" alt="" style={{ width: "100%", height: 120, objectFit: "cover", display: "block" }} />
          <div style={{ padding: "16px 28px" }}>
            {([["At the Finals", LT.finals], ["After a game", LT.game_day]] as const).map(([lab, v]) => (
              <div key={lab} style={{ marginBottom: 8 }}>
                <div className="font-cond" style={{ fontSize: 21, letterSpacing: "0.14em", color: C.gold, fontWeight: 700 }}>{lab.toUpperCase()}</div>
                <div style={{ display: "flex", gap: 26, alignItems: "baseline" }}>
                  <span className="font-display" style={{ fontSize: 54, color: TIER_COLOR.role }}>{Math.round(v.role * 100)}%</span>
                  <span style={{ fontSize: 20, color: C.muted }}>role</span>
                  <span className="font-display" style={{ fontSize: 54, color: TIER_COLOR.superstar }}>{Math.round(v.superstar * 100)}%</span>
                  <span style={{ fontSize: 20, color: C.muted }}>superstar</span>
                </div>
              </div>
            ))}
            <div style={{ fontSize: 21, color: C.muted }}>of each tier&apos;s press conferences</div>
            <Reveal show={step >= 2} y={12}>
              <div style={{ borderTop: "1px solid rgba(246,239,228,0.15)", marginTop: 10, paddingTop: 8 }}>
                <span className="font-display" style={{ fontSize: 46, color: C.gold }}>{LT.n_hold} of 10</span>
                <div style={{ fontSize: 21, lineHeight: 1.3 }}>gaps hold with round and game day equal: {hold.join(", ").toLowerCase()}</div>
                <div style={{ fontSize: 18, color: C.dim, marginTop: 8 }}>10 tests, no correction · topic shares are controls in the main model</div>
              </div>
            </Reveal>
          </div>
        </Card>
      </Reveal>
    </div>
  );
}

const KEY_TOPICS = new Set(["Individual performance", "Championship and legacy", "The Finals stage"]);

export function Topics({ step }: SlideProps) {
  const X = lin(0.05, 0.16, 600, 1240);
  const pick = usePick<number>(); // hover a topic for all three tiers
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Q3 · the questions" title="Reporters ask the tiers about different things" size={80} />
      <Legend style={{ position: "absolute", left: 600, top: 296 }} items={[
        { label: "Superstars", color: TIER_COLOR.superstar }, { label: "Role players", color: TIER_COLOR.role }]} />
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0 }}>
        {[0.06, 0.09, 0.12, 0.15].map((v) => (
          <g key={v}>
            <line x1={X(v)} x2={X(v)} y1={345} y2={905} stroke={C.grid} strokeWidth={1.5} />
            <text x={X(v)} y={940} textAnchor="middle" fontSize={22} fill={C.muted}>{Math.round(v * 100)}%</text>
          </g>
        ))}
        <text x={X(0.105)} y={975} textAnchor="middle" fontSize={22} fill={C.muted}>average share of the reporters&apos; questions on the topic</text>
        {R.topics.map((t, k) => {
          const y = 370 + k * 56;
          const focus = step < 1 || KEY_TOPICS.has(t.label);
          const a = X(t.role), b = X(t.superstar);
          return (
            <motion.g key={t.label} animate={{ opacity: focus ? 1 : 0.25 }}>
              <text x={570} y={y + 8} textAnchor="end" fontSize={25} fontWeight={focus && step >= 1 ? 700 : 500} fill={C.cream}>{t.label}</text>
              <motion.line y1={y} y2={y} stroke={C.cream} strokeOpacity={0.35} strokeWidth={5}
                initial={{ x1: (a + b) / 2, x2: (a + b) / 2 }} animate={{ x1: Math.min(a, b), x2: Math.max(a, b) }}
                transition={{ delay: 0.4 + k * 0.07, duration: 0.7, ease }} />
              {([["role", a], ["superstar", b]] as [Tier, number][]).map(([tier, x]) => (
                <motion.circle key={tier} cy={y} r={13} fill={TIER_COLOR[tier]} stroke={C.floor} strokeWidth={3}
                  initial={{ cx: (a + b) / 2 }} animate={{ cx: x }} transition={{ delay: 0.4 + k * 0.07, duration: 0.7, ease }} />
              ))}
              <rect x={280} y={y - 27} width={980} height={54} fill="transparent" {...pick.hover(k)} />
            </motion.g>
          );
        })}
      </svg>
      {R.topics.map((t, k) => (
        <Tip key={t.label} show={pick.active === k} x={(X(t.role) + X(t.superstar)) / 2} y={370 + k * 56 - 24} anchor="above">
          <b>{t.label}</b>
          <span style={{ color: C.muted }}> · share of the questions:</span>{" "}
          {TIERS.map((tier) => (
            <span key={tier} style={{ marginLeft: 12 }}>
              <span style={{ display: "inline-block", width: 13, height: 13, borderRadius: "50%", background: TIER_COLOR[tier], marginRight: 6 }} />
              {TIER_NAME[tier]} <b>{pct(t[tier])}%</b>
            </span>
          ))}
        </Tip>
      ))}
      <Reveal delay={0.5} style={{ position: "absolute", left: 1330, top: 300, width: 480 }}>
        <Card style={{ overflow: "hidden", height: 640 }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/img/press/room.jpg" alt="" style={{ width: "100%", height: 300, objectFit: "cover", display: "block" }} />
          <div style={{ padding: "22px 28px" }}>
            <Reveal show={step >= 1} y={14}>
              <div className="font-display" style={{ fontSize: 96, lineHeight: 0.9, color: TIER_COLOR.role }}>
                {Math.round(R.finals_share.role * 100)}%
              </div>
              <div style={{ fontSize: 25, lineHeight: 1.3 }}>
                of role-player press conferences are at the Finals, vs <b style={{ color: TIER_COLOR.superstar }}>{Math.round(R.finals_share.superstar * 100)}%</b> for superstars.
              </div>
              <div style={{ fontSize: 22, color: C.gold, marginTop: 12, fontWeight: 700 }}>→ topics and round are controls in the model</div>
            </Reveal>
          </div>
        </Card>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 15. Robustness */
const SHORT: Record<string, string> = {
  "Main result (model A, all controls)": "Main result (all controls)",
  "Superstar = All-NBA that season": "Superstar = All-NBA",
  "All-NBA, same player (fixed effects)": "All-NBA, same player",
  "Two groups: superstar vs everyone else": "Superstar vs everyone else",
  "Role players who were never All-Stars": "Never-All-Star role players",
  "Game days only": "Game days only",
  "Non-game days only": "Other days only",
  "Game days, same player (fixed effects)": "Game days, same player",
  "Non-game days, same player (fixed effects)": "Other days, same player",
  "NBA Finals only": "NBA Finals only",
  "Without LeBron James": "Without LeBron James",
  "Without the 10 most-interviewed players": "Without the 10 most-interviewed",
  "Question topics from LDA with K = 5": "5 question topics instead of 10",
  "Each unit weighted equally (linear model)": "Each unit weighted equally",
  "Season fixed effects (era)": "Season fixed effects (era)",
  "Counting words instead (the plain we-share)": "Counting words instead (we-share)",
};

export function Robustness({ step }: SlideProps) {
  const X = lin(-0.12, 0.16, 700, 1260);
  const rows = R.bert_main.robustness;
  const checks = rows.filter((r) => r.group !== "Main" && r.group !== "Measure");
  const nChecks = checks.length;
  const zeroIn = checks.filter((r) => r.lo < 0 && r.hi > 0).length;
  const S = R.bert_main.selection;
  const RY = (k: number) => 318 + k * 41;
  const pick = usePick<number>(); // hover a check for its estimate and 95% CI
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Q3 · does it hold up?" title={`${nChecks} checks: ${zeroIn} include zero`} />
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0 }}>
        {[-0.1, -0.05, 0, 0.05, 0.1, 0.15].map((v) => (
          <g key={v}>
            <line x1={X(v)} x2={X(v)} y1={300} y2={960} stroke={v === 0 ? C.cream : C.grid} strokeOpacity={v === 0 ? 0.55 : 1} strokeWidth={v === 0 ? 2.5 : 1.5} />
            <text x={X(v)} y={990} textAnchor="middle" fontSize={20} fill={C.muted}>{v === 0 ? "0" : pp(v, 0)}</text>
          </g>
        ))}
        {rows.map((r, k) => {
          const y = RY(k);
          const main = r.group === "Main";
          const alt = r.group === "Measure";
          const gd = r.check === "Game days only";
          const focus = step < 1 || gd || main;
          const col = gd && step >= 1 ? C.gold : alt ? C.muted : TIER_COLOR.superstar;
          return (
            <motion.g key={r.check} animate={{ opacity: focus ? 1 : 0.25 }}>
              {k > 0 && rows[k - 1].group !== r.group && <line x1={110} x2={1310} y1={y - 20} y2={y - 20} stroke={C.grid} strokeWidth={1} />}
              <text x={680} y={y + 7} textAnchor="end" fontSize={21} fontWeight={main || gd ? 700 : 500} fill={alt ? C.muted : C.cream}>{SHORT[r.check] ?? r.check}</text>
              <motion.line y1={y} y2={y} stroke={col} strokeWidth={main ? 6 : 4} strokeLinecap="round"
                initial={{ x1: X(r.diff), x2: X(r.diff), opacity: 0 }} animate={{ x1: X(r.lo), x2: X(r.hi), opacity: 1 }}
                transition={{ delay: 0.5 + k * 0.07, duration: 0.5 }} />
              <motion.circle cx={X(r.diff)} r={main ? 11 : 8.5} fill={col} stroke={C.floor} strokeWidth={2.5}
                initial={{ cy: y - 60, opacity: 0 }} animate={{ cy: y, opacity: 1 }}
                transition={{ delay: 0.3 + k * 0.07, type: "spring", stiffness: 200, damping: 12 }} />
              {(main || alt || (gd && step >= 1)) && (
                <text x={X(r.hi) + 12} y={y + 7} fontSize={20} fontWeight={700} fill={col}>{pp(r.diff)} {ciTxt(r.lo, r.hi)}</text>
              )}
              <rect x={110} y={y - 20} width={1200} height={41} fill="transparent" {...pick.hover(k)} />
            </motion.g>
          );
        })}
      </svg>
      {rows.map((r, k) => (
        <Tip key={r.check} show={pick.active === k} x={X(r.diff)} y={RY(k) - 18} anchor="above">
          {r.check}: <b>{pp(r.diff)} points</b> <span style={{ color: C.muted }}>95% CI {ciTxt(r.lo, r.hi)}</span>
        </Tip>
      ))}
      <Reveal show={step >= 2} style={{ position: "absolute", left: 1430, top: 300, width: 380 }}>
        <Card style={{ padding: "26px 28px", height: 660 }} glow={C.gold}>
          <div className="font-display" style={{ fontSize: 50, lineHeight: 1 }}>Why game days?</div>
          <p style={{ fontSize: 23, color: C.muted, lineHeight: 1.35, margin: "12px 0 16px" }}>
            Game-day points above the player&apos;s own playoff average:
          </p>
          {(["role", "starter", "superstar"] as Tier[]).map((t, k) => (
            <div key={t} style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 21, color: C.cream, fontWeight: 600 }}>{TIER_NAME[t]}s</div>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <motion.div initial={{ width: 0 }} animate={step >= 2 ? { width: (S[t].pts / 6) * 270 } : { width: 0 }}
                  transition={{ delay: 0.4 + k * 0.15, duration: 0.7, ease }}
                  style={{ height: 30, borderRadius: 6, background: TIER_COLOR[t] }} />
                <span className="font-display" style={{ fontSize: 36 }}>+{S[t].pts.toFixed(1)}</span>
              </div>
            </div>
          ))}
          <p style={{ fontSize: 24, lineHeight: 1.35, margin: "18px 0 0" }}>
            Role players get to the podium after <b>their own big games</b>.
          </p>
          <p style={{ fontSize: 24, lineHeight: 1.35, margin: "12px 0 0", color: C.gold, fontWeight: 700 }}>→ a pattern to note,<br />not a finding</p>
        </Card>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 16. "I" read in context (BERT, Step 17, exploratory) */
type Kind = "self" | "neither" | "team";
const KIND: { k: Kind; name: string; col: string }[] = [
  { k: "self", name: "self", col: C.i },
  { k: "neither", name: "conversation", col: C.dim },
  { k: "team", name: "team", col: C.we },
];
const KCOL = Object.fromEntries(KIND.map((d) => [d.k, d.col])) as Record<Kind, string>;
const KNAME = Object.fromEntries(KIND.map((d) => [d.k, d.name])) as Record<Kind, string>;

function Chip({ children, col, filled = false }: { children: ReactNode; col: string; filled?: boolean }) {
  return (
    <span className="font-cond" style={{ display: "inline-block", width: 158, textAlign: "center", padding: "4px 0", borderRadius: 999,
      border: `2px solid ${col}`, background: filled ? a(col, 0.24) : "transparent", color: C.cream, fontSize: 21, fontWeight: 700, letterSpacing: "0.05em" }}>
      {children}
    </span>
  );
}

export function InContext({ step }: SlideProps) {
  const B = R.bert;
  const pick = usePick<string>(); // hover or click an example (kind) or a bar segment (tier:kind): that kind lights up everywhere
  const act = pick.active;
  const kindOn = act ? (act.split(":").pop() as Kind) : null;
  const dim = (k: Kind) => (kindOn && kindOn !== k ? 0.28 : 1);
  const W = 470;
  const readout = !act ? (
    <>About the same mix in every tier.</>
  ) : act.includes(":") ? (
    <>{TIER_NAME[act.split(":")[0] as Tier]}s: <b>{pct(B.mix[act.split(":")[0] as Tier][kindOn!], 0)}%</b> of “I” words are {KNAME[kindOn!]}</>
  ) : (
    <>{KNAME[kindOn!]}: {TIERS.map((t) => `${pct(B.mix[t][kindOn!], 0)}%`).join(" · ")} <span style={{ color: C.muted }}>(role · starter · superstar)</span></>
  );
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Measuring self-focus · what BERT finds" title={`Read in context, ${pct(B.mix_all.neither, 0)}% of “I” is just conversation`} size={80} />
      {/* left: real uses of "I", as the we-share counts them and as BERT reads them */}
      <Reveal delay={0.25} style={{ position: "absolute", left: 110, top: 290, width: 860 }}>
        <Card style={{ padding: "20px 30px", height: 470 }}>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 12, paddingBottom: 10 }}>
            <div className="font-cond" style={{ flex: 1, fontSize: 21, letterSpacing: "0.14em", color: C.gold, fontWeight: 700 }}>REAL “I” WORDS</div>
            <div className="font-cond" style={{ width: 158, textAlign: "center", fontSize: 18, letterSpacing: "0.1em", color: C.muted, fontWeight: 700 }}>COUNTING SAYS</div>
            <motion.div className="font-cond" initial={false} animate={{ opacity: step >= 1 ? 1 : 0 }}
              style={{ width: 158, textAlign: "center", fontSize: 18, letterSpacing: "0.1em", color: C.muted, fontWeight: 700 }}>BERT READS</motion.div>
          </div>
          {KIND.map(({ k }, j) => {
            const e = B.examples[k];
            return (
              <motion.div key={k} className="tap" {...pick.bind(k)} animate={{ opacity: dim(k) }}
                style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 0", borderTop: `1px solid ${C.grid}` }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 27, lineHeight: 1.3 }}>
                    “{e.tokens.map((tk, n) => tk.k === "target"
                      ? <span key={n} style={{ color: C.i, background: a(C.i, 0.2), boxShadow: `inset 0 -3px 0 ${C.i}`, borderRadius: 6, padding: "0 4px", fontWeight: 700 }}>{tk.t}</span>
                      : <span key={n}>{tk.t}</span>)}”
                  </div>
                  <div style={{ fontSize: 18, color: C.muted, marginTop: 3 }}>{e.person} · {TIER_NAME[e.tier as Tier].toLowerCase()} · {e.season}</div>
                </div>
                <Chip col={C.i}>self-focus</Chip>
                <motion.div initial={false} animate={{ opacity: step >= 1 ? 1 : 0, scale: step >= 1 ? 1 : 0.8 }} transition={{ delay: step >= 1 ? 0.3 + j * 0.25 : 0 }}>
                  <Chip col={KCOL[k]} filled>{KNAME[k]}</Chip>
                </motion.div>
              </motion.div>
            );
          })}
          <div style={{ display: "flex", alignItems: "center", gap: 12, paddingTop: 12, borderTop: `1px solid ${C.grid}` }}>
            <div style={{ flex: 1, fontSize: 22, color: C.muted, lineHeight: 1.3 }}>
              Kobe, earlier: “It is not <b style={{ color: C.i }}>me</b> at the forefront.”
            </div>
            <Chip col={C.i}>self-focus</Chip>
            <motion.div initial={false} animate={{ opacity: step >= 1 ? 1 : 0, scale: step >= 1 ? 1 : 0.8 }} transition={{ delay: step >= 1 ? 1.1 : 0 }}>
              <Chip col={KCOL[B.kobe_me as Kind]} filled>{KNAME[B.kobe_me as Kind]}{B.kobe_me !== "team" ? " ✗" : ""}</Chip>
            </motion.div>
          </div>
        </Card>
      </Reveal>
      {/* right: every "I", by tier */}
      <Reveal show={step >= 1} style={{ position: "absolute", left: 1000, top: 290, width: 810 }}>
        <Card style={{ padding: "20px 30px", height: 470 }}>
          <div className="font-cond" style={{ fontSize: 21, letterSpacing: "0.14em", color: C.gold, fontWeight: 700 }}>
            ALL {B.n_i.toLocaleString("en-US")} “I” WORDS, READ IN CONTEXT
          </div>
          <Legend style={{ marginTop: 10, fontSize: 22 }} items={KIND.map((d) => ({ label: d.name, color: d.col }))} />
          <div style={{ marginTop: 22 }}>
            {TIERS.map((t, ti) => (
              <div key={t} style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 20 }}>
                <div style={{ width: 160, fontSize: 23, fontWeight: 600, display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ width: 14, height: 14, borderRadius: "50%", background: TIER_COLOR[t], flex: "none" }} />{TIER_NAME[t]}s
                </div>
                <div style={{ display: "flex", gap: 2, width: W }}>
                  {KIND.map(({ k, col }, j) => {
                    const v = B.mix[t][k];
                    return (
                      <motion.div key={k} className="tap" {...pick.bind(`${t}:${k}`)}
                        initial={{ width: 0 }} animate={step >= 1 ? { width: v * (W - 4), opacity: dim(k) } : { width: 0 }}
                        transition={{ width: { delay: 0.4 + ti * 0.12 + j * 0.1, duration: 0.7, ease }, opacity: { duration: 0.3 } }}
                        style={{ height: 58, background: col, borderRadius: j === 0 ? "6px 0 0 6px" : j === 2 ? "0 6px 6px 0" : 0, display: "flex",
                          alignItems: "center", justifyContent: "center", overflow: "hidden", fontSize: 22, fontWeight: 700,
                          color: k === "neither" ? C.cream : C.ink }}>
                        {k !== "team" && `${pct(v, 0)}%`}
                      </motion.div>
                    );
                  })}
                </div>
                <motion.span animate={{ opacity: dim("team") }} style={{ fontSize: 22, fontWeight: 700, color: C.cream }}>{pct(B.mix[t].team, 0)}%</motion.span>
              </div>
            ))}
          </div>
          <div style={{ fontSize: 26, lineHeight: 1.35, minHeight: 70 }}>{readout}</div>
          <div style={{ fontSize: 20, color: C.muted, marginTop: 6 }}>Share of each tier&apos;s “I” words, as labelled by the classifier</div>
        </Card>
      </Reveal>
      {/* bottom: the main measure built from the labels */}
      <Reveal show={step >= 2} style={{ position: "absolute", left: 110, top: 778, width: 1700 }}>
        <Card style={{ height: 142, padding: "14px 34px", display: "flex", alignItems: "center", gap: 34 }} glow={C.gold}>
          <div style={{ width: 360, flex: "none" }}>
            <div className="font-cond" style={{ fontSize: 22, letterSpacing: "0.14em", color: C.gold, fontWeight: 700 }}>THE MAIN MEASURE</div>
            <div style={{ fontSize: 20, color: C.muted, lineHeight: 1.35, marginTop: 6 }}>per player, per press conference; same models and controls as before</div>
          </div>
          <div>
            <div className="font-display" style={{ fontSize: 40, lineHeight: 1.1 }}>
              team-focused share = (<span style={{ color: C.we }}>team “I”</span> + <span style={{ color: C.we }}>“we”</span>) ÷
              (<span style={{ color: C.i }}>self “I”</span> + <span style={{ color: C.we }}>team “I”</span> + <span style={{ color: C.we }}>“we”</span>)
            </div>
            <div style={{ fontSize: 22, color: C.muted, marginTop: 6 }}>
              Conversation “I” is left out · every “we” counts as team (next slide)
            </div>
          </div>
        </Card>
      </Reveal>
      <Reveal show={step >= 2} delay={0.3} style={{ position: "absolute", left: 110, top: 940, width: 1700 }}>
        <div style={{ fontSize: 21, color: C.muted, textAlign: "center" }}>
          Misses about half of credit-giving “I” ({B.classifier.team_found} of {B.classifier.team_total}){B.kobe_me !== "team" ? ", Kobe's too" : ""} ·
          made the main measure after a first analysis (both measures agree)
        </div>
      </Reveal>
    </div>
  );
}
