"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { Card, Header, Headshot, Kicker, Quote, Reveal, stop, Tap, TierPill, Title } from "@/components/ui";
import { C, ease, P, R, Tier, TIER_COLOR } from "@/lib/theme";
import { SlideProps } from "./types";

/* ------------------------------------------------------------------ 1. Title with a jump shot */
const arc = Array.from({ length: 25 }, (_, k) => {
  const t = k / 24;
  return [(1 - t) ** 2 * 40 + 2 * (1 - t) * t * 300 + t * t * 600, (1 - t) ** 2 * 640 + 2 * (1 - t) * t * -260 + t * t * 190];
});
const tail = [[600, 330], [618, 660], [635, 545], [650, 660], [660, 625], [668, 660]];
const SHOT = {
  x: [...arc.map((p) => p[0]), ...tail.map((p) => p[0])],
  y: [...arc.map((p) => p[1]), ...tail.map((p) => p[1])],
  times: [...arc.map((_, k) => (k / 24) * 0.55), 0.62, 0.75, 0.84, 0.92, 0.96, 1],
};
const SHOT_DELAY = 0.9, SHOT_DUR = 2.6, SWISH = SHOT_DELAY + 0.55 * SHOT_DUR;

function Hoop() {
  const [shots, setShots] = useState(0); // click the hoop to shoot again
  const delay = shots === 0 ? SHOT_DELAY : 0.05;
  const swish = delay + 0.55 * SHOT_DUR;
  const draw = (d: number) => ({ initial: { pathLength: 0 }, animate: { pathLength: 1 }, transition: { duration: 0.9, delay: d } });
  const drawOnce = (d: number) => (shots === 0 ? draw(d) : {});
  const net = Array.from({ length: 7 }, (_, k) => ({ x1: 540 + k * 20, x2: 565 + (k * 70) / 6 }));
  return (
    <svg width="800" height="720" style={{ position: "absolute", left: 1090, top: 150, overflow: "visible" }}>
      <motion.line x1="600" y1="180" x2="600" y2="700" stroke={C.cream} strokeOpacity="0.22" strokeWidth="10" {...draw(0)} />
      <motion.rect x="500" y="40" width="200" height="140" rx="8" fill="rgba(246,239,228,0.07)" stroke={C.cream} strokeWidth="5" {...draw(0.1)} />
      <motion.rect x="560" y="110" width="80" height="58" fill="none" stroke={C.ball} strokeWidth="5" {...draw(0.3)} />
      <line x1="0" y1="700" x2="800" y2="700" stroke={C.cream} strokeOpacity="0.15" strokeWidth="3" />
      {/* ball: translate on the outer group, spin on the inner one */}
      <motion.g
        key={`ball${shots}`}
        initial={{ x: 40, y: 640, opacity: 0 }}
        animate={{ x: SHOT.x, y: SHOT.y, opacity: 1 }}
        transition={{ x: { duration: SHOT_DUR, times: SHOT.times, delay, ease: "linear" },
          y: { duration: SHOT_DUR, times: SHOT.times, delay, ease: "linear" },
          opacity: { duration: 0.2, delay } }}
      >
        <motion.g animate={{ rotate: 720 }} transition={{ duration: SHOT_DUR, delay, ease: "linear" }}
          style={{ originX: 0.5, originY: 0.5 }}>
          <circle r="40" fill={C.ball} stroke="#2a1408" strokeWidth="3" />
          <g fill="none" stroke="#2a1408" strokeWidth="3" strokeLinecap="round">
            <path d="M0 -40 V40" /><path d="M-40 0 H40" />
            <path d="M-28 -29 C-12 -12 -12 12 -28 29" /><path d="M28 -29 C12 -12 12 12 28 29" />
          </g>
        </motion.g>
      </motion.g>
      <motion.g
        key={`net${shots}`}
        style={{ originX: 0.5, originY: 0 }}
        animate={{ scaleY: [1, 1.32, 0.9, 1.06, 1] }}
        transition={{ delay: swish, duration: 0.7 }}
      >
        {net.map((n, k) => (
          <motion.line key={k} x1={n.x1} y1="200" x2={n.x2} y2="300" stroke={C.cream} strokeWidth="3" strokeOpacity="0.85" {...drawOnce(0.5)} />
        ))}
        {net.slice(0, -1).map((n, k) => (
          <motion.path key={`d${k}`} d={`M${n.x1} 200 L${net[k + 1].x2} 300 M${net[k + 1].x1} 200 L${n.x2} 300`}
            stroke={C.cream} strokeWidth="2" strokeOpacity="0.5" fill="none" {...drawOnce(0.6)} />
        ))}
      </motion.g>
      <motion.ellipse cx="600" cy="200" rx="62" ry="12" fill="none" stroke={C.ball} strokeWidth="8" {...draw(0.4)} />
      <motion.text
        key={`pts${shots}`}
        x="700" y="0" fontSize="70" fill={C.gold} className="font-display"
        initial={{ opacity: 0, y: 190 }} animate={{ opacity: [0, 1, 1, 0], y: [190, 140, 120, 100] }}
        transition={{ delay: swish + 0.05, duration: 1.6, times: [0, 0.2, 0.7, 1] }}
      >
        +2
      </motion.text>
      {/* click target: backboard, rim and net */}
      <rect x="470" y="20" width="260" height="300" fill="transparent" className="tap" onClick={stop(() => setShots((n) => n + 1))} />
    </svg>
  );
}

const LINEUP: { p: (typeof P)[keyof typeof P]; tier: Tier }[] = [
  { p: P.ginobili, tier: "role" }, { p: P.iguodala, tier: "role" }, { p: P.caruso, tier: "role" },
  { p: P.holiday, tier: "starter" }, { p: P.horford, tier: "starter" },
  { p: P.curry, tier: "superstar" }, { p: P.kobe, tier: "superstar" }, { p: P.lebron, tier: "superstar" },
];

export function TitleSlide() {
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <div style={{ position: "absolute", left: 110, top: 150, width: 1060 }}>
        <Kicker>HG4054 final project · Travis Ang</Kicker>
        <div style={{ height: 18 }} />
        <Title text="Are superstars more self-focused than role players?" size={128} delay={0.2} />
        <Reveal delay={1.0} y={16}>
          <p style={{ fontSize: 36, color: C.muted, margin: "26px 0 0", fontWeight: 500 }}>
            &ldquo;I&rdquo; versus &ldquo;we&rdquo; in {R.sample.press_conferences.toLocaleString()} NBA playoff press conferences, 2004&ndash;2026
          </p>
        </Reveal>
      </div>
      <Hoop />
      <div style={{ position: "absolute", left: 110, top: 760, display: "flex", gap: 26 }}>
        {LINEUP.map(({ p, tier }, k) => (
          <motion.div key={p.id} initial={{ opacity: 0, y: 50, scale: 0.8 }} animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: SWISH + 0.25 + k * 0.08, type: "spring", stiffness: 160, damping: 14 }}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10, width: 118 }}>
            <Headshot id={p.id} size={112} ring={TIER_COLOR[tier]} />
            <span className="font-cond" style={{ fontSize: 17, color: C.muted, fontWeight: 600, textAlign: "center", lineHeight: 1.1 }}>{p.name}</span>
          </motion.div>
        ))}
      </div>
      <Reveal delay={SWISH + 1.0} y={10} style={{ position: "absolute", left: 110, top: 940, display: "flex", gap: 18 }}>
        <TierPill tier="role" size={18} />
        <TierPill tier="starter" size={18} />
        <TierPill tier="superstar" size={18} />
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 2. Guess who said it */
function Mystery() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 22 }}>
      <div style={{ width: 104, height: 104, borderRadius: "50%", background: C.surface2, display: "grid", placeItems: "center",
        border: `3px dashed ${C.dim}` }}>
        <span className="font-display" style={{ fontSize: 64, color: C.muted }}>?</span>
      </div>
      <span className="font-display" style={{ fontSize: 46, color: C.muted }}>Superstar or role player?</span>
    </div>
  );
}

function QuoteCard({ q, p, step, left, delay, open, onTap }: {
  q: typeof R.quotes.hook_we; p: (typeof P)[keyof typeof P]; step: number; left: number; delay: number; open: boolean; onTap: () => void;
}) {
  const shown = step >= 2 || open;
  return (
    <Reveal delay={delay} style={{ position: "absolute", left, top: 300, width: 820 }}>
      <Tap onTap={onTap} className="tap-lift">
      <Card style={{ height: 560, padding: "34px 44px", position: "relative" }} glow={open && step < 2 ? C.gold : undefined}>
        <div className="font-display" style={{ position: "absolute", right: 36, top: 10, fontSize: 200, color: "rgba(246,239,228,0.08)", lineHeight: 1 }}>&rdquo;</div>
        <Reveal show={step >= 1} y={-10} style={{ display: "flex", gap: 14, marginBottom: 20 }}>
          <span className="font-display" style={{ fontSize: 36, color: C.i, border: `2px solid ${C.i}`, borderRadius: 10, padding: "0 14px" }}>&ldquo;I&rdquo; words × {q.i}</span>
          <span className="font-display" style={{ fontSize: 36, color: C.we, border: `2px solid ${C.we}`, borderRadius: 10, padding: "0 14px" }}>&ldquo;we&rdquo; words × {q.we}</span>
        </Reveal>
        <Quote tokens={q.tokens} iOn={step >= 1} weOn={step >= 1} size={38} />
        <div style={{ position: "absolute", left: 44, bottom: 34, right: 44 }}>
          <AnimatePresence mode="wait" initial={false}>
            {!shown ? (
              <motion.div key="m" exit={{ rotateX: 90, opacity: 0 }} transition={{ duration: 0.3 }}><Mystery /></motion.div>
            ) : (
              <motion.div key="r" initial={{ rotateX: -90, opacity: 0 }} animate={{ rotateX: 0, opacity: 1 }} transition={{ duration: 0.45, ease }}
                style={{ display: "flex", alignItems: "center", gap: 22 }}>
                <Headshot id={p.id} size={104} ring={TIER_COLOR[q.tier as Tier]} />
                <div>
                  <div className="font-display" style={{ fontSize: 50, lineHeight: 1 }}>{p.name}</div>
                  <div style={{ display: "flex", gap: 14, alignItems: "center", marginTop: 8 }}>
                    <TierPill tier={q.tier as Tier} size={19} />
                    <span style={{ fontSize: 22, color: C.muted }}>{q.season} playoffs</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </Card>
      </Tap>
    </Reveal>
  );
}

export function Hook({ step }: SlideProps) {
  const [open, setOpen] = useState([false, false]); // click a card to reveal who said it
  const flip = (k: number) => () => setOpen((o) => o.map((v, j) => (j === k ? !v : v)));
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Two real answers from the data" title="Guess: superstar or role player?" />
      <QuoteCard q={R.quotes.hook_we} p={P.lebron} step={step} left={110} delay={0.3} open={open[0]} onTap={flip(0)} />
      <QuoteCard q={R.quotes.hook_i} p={P.livingston} step={step} left={990} delay={0.45} open={open[1]} onTap={flip(1)} />
      <Reveal show={step >= 2} delay={0.5} style={{ position: "absolute", left: 110, top: 900, width: 1700 }}>
        <p style={{ fontSize: 34, margin: 0, color: C.cream }}>
          Two hand-picked answers prove nothing, so I collected <b style={{ color: C.gold }}>{R.sample.player_answers.toLocaleString()}</b>.
        </p>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 3. Two opposite predictions */
function Seesaw({ tilt, level, onTip }: { tilt: number; level: boolean; onTip: (v: number) => void }) {
  return (
    <svg width="900" height="250" style={{ position: "absolute", left: 510, top: 285, overflow: "visible" }}>
      <path d="M450 150 L400 235 H500 Z" fill={C.surface2} stroke={C.cream} strokeOpacity="0.5" strokeWidth="3" />
      <motion.g animate={{ rotate: tilt }} transition={{ type: "spring", stiffness: 70, damping: 9 }}
        style={{ originX: 0.5, originY: 0.93 }}>
        <rect x="90" y="140" width="720" height="18" rx="9" fill={C.gold} />
        <g className="tap" onClick={stop(() => onTip(-11))}>
          <circle cx="140" cy="88" r="52" fill={C.i} />
          <text x="140" y="108" textAnchor="middle" fontSize="60" className="font-display" fill="#140b24">I</text>
        </g>
        <g className="tap" onClick={stop(() => onTip(11))}>
          <circle cx="760" cy="88" r="52" fill={C.we} />
          <text x="760" y="108" textAnchor="middle" fontSize="54" className="font-display" fill="#062a33">WE</text>
        </g>
      </motion.g>
      <AnimatePresence>
        {level && (
          <motion.text key="q" x="450" y="80" textAnchor="middle" fontSize="110" className="font-display" fill={C.cream}
            initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}>?</motion.text>
        )}
      </AnimatePresence>
    </svg>
  );
}

export function Predictions({ step }: SlideProps) {
  const [tip, setTip] = useState<{ s: number; v: number } | null>(null); // click I or WE to tip it by hand
  const tilt = tip && tip.s === step ? tip.v : step === 0 ? -11 : step === 1 ? 11 : 0;
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="The question" title="Does status show up in how people talk?" />
      <Seesaw tilt={tilt} level={step >= 2 && !(tip && tip.s === step)} onTip={(v) => setTip({ s: step, v })} />
      <Reveal delay={0.4} style={{ position: "absolute", left: 110, top: 560, width: 780 }}>
        <Card style={{ padding: "30px 38px", height: 290 }} glow={step === 0 ? C.i : undefined}>
          <div className="font-cond" style={{ fontSize: 24, letterSpacing: "0.18em", color: C.i, fontWeight: 700 }}>COMMON BELIEF</div>
          <div className="font-display" style={{ fontSize: 58, lineHeight: 1, margin: "10px 0 14px" }}>Stars are more self-focused</div>
          <p style={{ fontSize: 30, color: C.muted, margin: 0, lineHeight: 1.35 }}>
            In the spotlight, stars talk about themselves: more &ldquo;I&rdquo;, less &ldquo;we&rdquo;.
          </p>
        </Card>
      </Reveal>
      <Reveal show={step >= 1} style={{ position: "absolute", left: 1030, top: 560, width: 780 }}>
        <Card style={{ padding: "30px 38px", height: 290 }} glow={step === 1 ? C.we : undefined}>
          <div className="font-cond" style={{ fontSize: 24, letterSpacing: "0.18em", color: C.we, fontWeight: 700 }}>LAB STUDIES · KACEWICZ ET AL. (2014)</div>
          <div className="font-display" style={{ fontSize: 58, lineHeight: 1, margin: "10px 0 14px" }}>Higher status, more &ldquo;we&rdquo;</div>
          <p style={{ fontSize: 30, color: C.muted, margin: 0, lineHeight: 1.35 }}>
            Five studies: higher-status people said fewer &ldquo;I&rdquo; words and more &ldquo;we&rdquo; words.
          </p>
        </Card>
      </Reveal>
      <Reveal show={step >= 2} style={{ position: "absolute", left: 110, top: 878, width: 1700 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 26 }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/img/press/podium.jpg" alt="" style={{ width: 150, height: 100, objectFit: "cover", borderRadius: 12, border: `2px solid ${C.gold}` }} />
          <p style={{ fontSize: 30, margin: 0, lineHeight: 1.3 }}>
            <b style={{ color: C.gold }}>Test it in real speech:</b> NBA playoff press conferences, where status is public and answers are unscripted.
            <br />
            <span style={{ color: C.muted }}>My prediction: superstars use relatively more &ldquo;we&rdquo; (tested in both directions).</span>
          </p>
        </div>
      </Reveal>
    </div>
  );
}
