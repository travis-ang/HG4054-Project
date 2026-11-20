"use client";

import { motion } from "framer-motion";
import { Card, CountUp, Header, Headshot, Quote, Reveal, TierPill, Tip, usePick } from "@/components/ui";
import { a, C, ease, lin, P, pct, pp, R, Tier, TIER_COLOR, TIER_NAME } from "@/lib/theme";
import { SlideProps } from "./types";

/* ------------------------------------------------------------------ 4. Pipeline */
const NODES = [
  { tag: "Scrape", n: R.sample.interviews_scraped, dec: 0, suf: "", unit: "press-conference transcripts",
    detail: "ASAP Sports, 2004–2026: every NBA playoff round on the site" },
  { tag: "Clean", n: R.sample.player_answers, dec: 0, suf: "", unit: "player answers in the playoffs",
    detail: "Removed moderators' lines and coaches (they are not on the status ladder)" },
  { tag: "Match", n: R.sample.matched_pct, dec: 1, suf: "%", unit: "matched to NBA records",
    detail: "stats.nba.com (nba_api): results, points, minutes, starts · Wikipedia: All-Stars" },
  { tag: "Build", n: R.sample.units, dec: 0, suf: "", unit: "units: one player in one press conference",
    detail: `${R.sample.press_conferences.toLocaleString()} press conferences · ${R.sample.players} players · ${R.bert_main.model_units.toLocaleString()} go into the model` },
];

export function Pipeline({ step }: SlideProps) {
  const X = (k: number) => 110 + k * 447;
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="The data" title={`From transcripts to ${R.sample.units.toLocaleString()} data points`} />
      {NODES.map((nd, k) => (
        <Reveal key={k} show={step >= k} delay={0.1} y={40} style={{ position: "absolute", left: X(k), top: 320, width: 360 }}>
          <Card style={{ height: 470, padding: "28px 30px", position: "relative", overflow: "hidden" }} glow={step === k ? C.gold : undefined}>
            <div style={{ position: "relative" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <span className="font-display" style={{ width: 52, height: 52, borderRadius: "50%", background: C.gold, color: C.ink,
                  display: "grid", placeItems: "center", fontSize: 34 }}>{k + 1}</span>
                <span className="font-cond" style={{ fontSize: 26, letterSpacing: "0.2em", fontWeight: 700, color: C.gold }}>{nd.tag.toUpperCase()}</span>
              </div>
              <div className="font-display" style={{ fontSize: 112, lineHeight: 1, marginTop: 44, color: C.cream }}>
                <CountUp to={nd.n} decimals={nd.dec} suffix={nd.suf} show={step >= k} />
              </div>
              <div style={{ fontSize: 29, fontWeight: 600, lineHeight: 1.2, marginTop: 6 }}>{nd.unit}</div>
              <div style={{ fontSize: 22, color: C.muted, lineHeight: 1.35, marginTop: 16 }}>{nd.detail}</div>
            </div>
          </Card>
        </Reveal>
      ))}
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
        {[0, 1, 2].map((k) => (
          <g key={k}>
            <motion.path d={`M${X(k) + 372} 555 L${X(k + 1) - 12} 555`} stroke={C.gold} strokeWidth={4} strokeDasharray="10 10"
              initial={{ pathLength: 0, opacity: 0 }} animate={step > k ? { pathLength: 1, opacity: 1 } : { pathLength: 0, opacity: 0 }}
              transition={{ duration: 0.5 }} />
            <motion.path d={`M${X(k + 1) - 26} 543 L${X(k + 1) - 12} 555 L${X(k + 1) - 26} 567`} fill="none" stroke={C.gold} strokeWidth={4}
              initial={{ opacity: 0 }} animate={{ opacity: step > k ? 1 : 0 }} transition={{ delay: 0.4 }} />
          </g>
        ))}
      </svg>
      <Reveal show={step >= 3} delay={0.9} style={{ position: "absolute", left: 110, top: 822, width: 1700, display: "flex", gap: 30, alignItems: "center" }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/img/press/reporters.jpg" alt="" style={{ width: 300, height: 150, objectFit: "cover", objectPosition: "35% 100%",
          borderRadius: 14, border: `2px solid ${C.gold}`, flex: "none" }} />
        <p style={{ fontSize: 28, color: C.muted, margin: 0, lineHeight: 1.45 }}>
          <b style={{ color: C.cream }}>Why this data?</b> Status is public and objective (All-Star picks, starts), the speech is unscripted,
          and the same players answer reporters year after year. <b style={{ color: C.cream }}>Self-collected:</b> scraped and labelled for this project.
        </p>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 5. Status tiers */
const BLOCKS: { tier: Tier; x: number; h: number; rule: string; faces: number[] }[] = [
  { tier: "role", x: 140, h: 220, rule: "Started under half of regular-season games", faces: [P.ginobili.id, P.iguodala.id, P.livingston.id] },
  { tier: "starter", x: 700, h: 330, rule: "Started at least half of regular-season games", faces: [P.holiday.id, P.horford.id, P.billups.id] },
  { tier: "superstar", x: 1260, h: 440, rule: "All-Star that season (incl. injured picks)", faces: [P.curry.id, P.kobe.id, P.lebron.id] },
];

const NAME_OF = Object.fromEntries(Object.values(P).map((p) => [p.id, p.name]));

export function Tiers({ step }: SlideProps) {
  const T = R.sample.tiers;
  const pick = usePick<number>(); // hover a face to see the name
  const share = (t: Tier) => Math.round((100 * T[t].game_day) / T[t].units);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Who counts as what" title="Three tiers of status, set each season" />
      {BLOCKS.map((b, k) => (
        <div key={b.tier}>
          <motion.div
            initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={{ delay: 0.3 + k * 0.18, duration: 0.8, ease }}
            style={{
              position: "absolute", left: b.x, top: 960 - b.h, width: 500, height: b.h, originY: 1, borderRadius: "18px 18px 0 0",
              background: `linear-gradient(180deg, ${TIER_COLOR[b.tier]}f0, ${TIER_COLOR[b.tier]}70)`,
              borderTop: `5px solid ${TIER_COLOR[b.tier]}`, padding: "20px 26px", boxShadow: `0 0 50px ${TIER_COLOR[b.tier]}40`,
            }}
          >
            <div className="font-display" style={{ fontSize: 58, lineHeight: 1, color: "#fff" }}>{TIER_NAME[b.tier]}s</div>
            <div style={{ fontSize: 22, color: "#fff", opacity: 0.92, marginTop: 6, fontWeight: 500 }}>{b.rule}</div>
            <Reveal show={step >= 1} delay={0.2 + k * 0.1} y={12}>
              <div className="font-display" style={{ fontSize: 44, color: "#fff", marginTop: 12, lineHeight: 1 }}>
                <CountUp to={T[b.tier].units} show={step >= 1} /> <span style={{ fontSize: 26 }}>units</span>
                <span style={{ margin: "0 12px", opacity: 0.6 }}>·</span>
                <CountUp to={T[b.tier].players} show={step >= 1} /> <span style={{ fontSize: 26 }}>players</span>
              </div>
            </Reveal>
          </motion.div>
          <div style={{ position: "absolute", left: b.x + 250 - 155, top: 960 - b.h - 122, display: "flex" }}>
            {b.faces.map((id, j) => (
              <motion.div key={id} initial={{ opacity: 0, y: 30, scale: 0.6 }}
                animate={step >= 1 ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: 30, scale: 0.6 }}
                transition={{ delay: step >= 1 ? 0.15 + k * 0.15 + j * 0.07 : 0, type: "spring", stiffness: 170, damping: 14 }}
                style={{ marginLeft: j ? -12 : 0, position: "relative", zIndex: pick.active === id ? 2 : 1 }} {...pick.hover(id)}>
                <Headshot id={id} size={110} ring={TIER_COLOR[b.tier]} />
              </motion.div>
            ))}
          </div>
          {b.faces.map((id, j) => (
            <Tip key={id} show={step >= 1 && pick.active === id} x={b.x + 95 + j * 98 + 55} y={960 - b.h - 132} anchor="above" accent={TIER_COLOR[b.tier]}>
              <b>{NAME_OF[id]}</b>
            </Tip>
          ))}
        </div>
      ))}
      {/* a player who switches tier */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={step >= 2 ? { opacity: 1, x: [0, 300, 560], y: [0, -170, -196] } : { opacity: 0, x: 0, y: 0 }}
        transition={{ duration: step >= 2 ? 1.6 : 0.2, ease: "easeInOut", times: [0, 0.5, 1] }}
        style={{ position: "absolute", left: 900, top: 470, display: "flex", alignItems: "center", gap: 14 }}
      >
        <Headshot id={P.draymond.id} size={96} ring={C.gold} />
      </motion.div>
      <Reveal show={step >= 2} delay={1.5} x={-10} y={0} style={{ position: "absolute", left: 1570, top: 286, width: 250 }}>
        <div style={{ fontSize: 22, color: C.cream, lineHeight: 1.25 }}>
          <b>Draymond Green</b><br /><span style={{ color: C.muted }}>starter seasons and All-Star seasons</span>
        </div>
      </Reveal>
      <div style={{ position: "absolute", left: 110, top: 296, width: 640, display: "flex", flexDirection: "column", gap: 14 }}>
        {[
          <><b style={{ color: C.gold }}>{R.sample.tier_changers}</b> players change tier between seasons</>,
          <>Superstars talk more: median <b style={{ color: C.gold }}>{R.sample.median_words.superstar}</b> vs <b style={{ color: C.gold }}>{R.sample.median_words.role}</b> words</>,
          <>Post-game share: superstars <b style={{ color: C.gold }}>{share("superstar")}%</b>, role players <b style={{ color: C.gold }}>{share("role")}%</b></>,
        ].map((t, k) => (
          <Reveal key={k} show={step >= 2} delay={0.2 + k * 0.15} x={-24} y={0}>
            <div style={{ fontSize: 25, padding: "10px 18px", borderLeft: `4px solid ${C.gold}`, background: "rgba(28,21,16,0.88)", borderRadius: 8 }}>{t}</div>
          </Reveal>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ 6. Counting words: the obvious measure and its problem */
const LOVE = R.we_examples.starter.find((x) => x.person === "Kevin Love" && x.season === 2016)!;
const marked = (tokens: { t: string; k: string }[], col: string) => tokens.map((tk, j) => tk.k === "target"
  ? <b key={j} style={{ color: col, background: a(col, 0.2), borderRadius: 6, padding: "0 4px" }}>{tk.t}</b>
  : <span key={j}>{tk.t}</span>);
const PROBLEMS = [
  { head: "“I think”, “I mean”", body: "conversation, not self-focus", stat: `${pct(R.bert.mix_all.neither, 0)}% of all “I”`,
    ex: R.bert.examples.neither, col: C.i },
  { head: "“It's not about me”", body: "gives the credit away", stat: `${pct(R.bert.mix_all.team, 0)}% of all “I”`,
    ex: R.bert.examples.team, col: C.i },
  { head: "“…to protect us”", body: "a “we” that is not the team", stat: `about 1 in 10 “we”`,
    ex: { person: LOVE.person, season: LOVE.season, tokens: LOVE.tokens }, col: C.we },
];

export function Measure({ step }: SlideProps) {
  const q = R.quotes.measure;
  const pick = usePick<number>(); // hover or click a problem for a real example
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Measuring self-focus · the obvious way" title="Counting “I” and “we” misses what they mean" size={80} />
      <Reveal delay={0.25} style={{ position: "absolute", left: 110, top: 290, width: 1080 }}>
        <Card style={{ padding: "30px 40px", height: 470, position: "relative" }}>
          <Quote tokens={q.tokens} iOn={step >= 1} weOn={step >= 1} size={40} />
          <div style={{ position: "absolute", left: 40, bottom: 24, display: "flex", alignItems: "center", gap: 18 }}>
            <Headshot id={P.kobe.id} size={70} ring={TIER_COLOR.superstar} />
            <span style={{ fontSize: 24, color: C.muted }}><b style={{ color: C.cream }}>Kobe Bryant</b> · superstar · {q.season} conference finals</span>
          </div>
        </Card>
      </Reveal>
      <Reveal show={step >= 1} style={{ position: "absolute", left: 1250, top: 290, width: 560 }}>
        <Card style={{ height: 470, padding: "26px 32px" }}>
          <div className="font-cond" style={{ fontSize: 22, letterSpacing: "0.14em", color: C.gold, fontWeight: 700 }}>COUNT THE WORDS</div>
          <div style={{ display: "flex", gap: 22, marginTop: 14 }}>
            {([["i", "“I” words", C.i, q.i], ["we", "“we” words", C.we, q.we]] as const).map(([k, label, col, n]) => (
              <div key={k} style={{ flex: 1, textAlign: "center", border: `2px solid ${col}`, borderRadius: 18, padding: "8px 0" }}>
                <div className="font-cond" style={{ fontSize: 22, color: col, fontWeight: 700, letterSpacing: "0.08em" }}>{label}</div>
                <div className="font-display" style={{ fontSize: 92, lineHeight: 1, color: col }}>{n}</div>
              </div>
            ))}
          </div>
          <div className="font-display" style={{ fontSize: 46, lineHeight: 1.1, marginTop: 22 }}>
            <span style={{ color: C.we }}>we</span> ÷ (<span style={{ color: C.i }}>I</span> + <span style={{ color: C.we }}>we</span>)
            {" "}= <span style={{ color: C.gold }}>{(q.we / (q.i + q.we)).toFixed(2)}</span>
          </div>
          <p style={{ fontSize: 25, color: C.muted, lineHeight: 1.4, margin: "18px 0 0" }}>
            The <b style={{ color: C.cream }}>“we-share”</b> calls this half self-focused, for an answer that is all about the team.
          </p>
        </Card>
      </Reveal>
      <div style={{ position: "absolute", left: 110, top: 790, width: 1700, display: "flex", gap: 24 }}>
        {PROBLEMS.map((pr, k) => (
          <Reveal key={k} show={step >= 2} delay={0.15 + k * 0.15} y={30} style={{ flex: 1 }}>
            <div className="tap" {...pick.bind(k)} style={{ height: 150, padding: "16px 24px", borderRadius: 18, background: "rgba(28,21,16,0.92)",
              border: `2px solid ${pick.active === k ? C.gold : "rgba(246,239,228,0.14)"}`, borderLeft: `6px solid ${pr.col}`, transition: "border-color .2s" }}>
              <div style={{ fontSize: 30, fontWeight: 700 }}>{pr.head}</div>
              <div style={{ fontSize: 23, color: C.muted, marginTop: 4 }}>{pr.body}, but counted</div>
              <div className="font-cond" style={{ fontSize: 22, color: C.gold, fontWeight: 700, letterSpacing: "0.06em", marginTop: 8 }}>{pr.stat}</div>
            </div>
          </Reveal>
        ))}
      </div>
      {PROBLEMS.map((pr, k) => (
        <Tip key={k} show={step >= 2 && pick.active === k} x={110 + k * 575 + 280} y={780} anchor="above" width={560} accent={pr.col}>
          <div style={{ fontSize: 23, lineHeight: 1.4 }}>&ldquo;{marked(pr.ex.tokens, pr.col)}&rdquo;</div>
          <div style={{ fontSize: 18, color: C.muted, marginTop: 6 }}>{pr.ex.person} · {pr.ex.season} playoffs · a real answer</div>
        </Tip>
      ))}
      <Reveal show={step >= 2} delay={0.7} style={{ position: "absolute", left: 110, top: 955, width: 1700 }}>
        <div style={{ fontSize: 20, color: C.muted, textAlign: "center" }}>
          Shares from the BERT labels and the “we” check, coming up · <b style={{ color: C.gold }}>so: read each word in its sentence</b>
        </div>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 7. Does "we" mean the team? */
const REFERENT: Record<string, string> = { team: "the player's team", other_group: "another group", generic: "a generic “we”" };

export function WeCheck({ step }: SlideProps) {
  const rows: Tier[] = ["superstar", "starter", "role"];
  const W = R.we_check;
  const pick = usePick<string>(); // hover or click a dot to read that use of "we"
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Checking “we”" title="About 9 in 10 uses of “we” mean the team" />
      <Reveal delay={0.3} y={0} style={{ position: "absolute", left: 440, top: 292 }}>
        <div style={{ display: "flex", gap: 34, fontSize: 24, color: C.muted, alignItems: "center" }}>
          <span><span style={{ display: "inline-block", width: 20, height: 20, borderRadius: "50%", background: C.cream, verticalAlign: "-3px", marginRight: 10 }} />the player&apos;s team</span>
          <span><span style={{ display: "inline-block", width: 20, height: 20, borderRadius: "50%", border: `3px solid ${C.cream}`, verticalAlign: "-3px", marginRight: 10 }} />another group, or a generic “we”</span>
          <span>· 30 random uses per tier, one per player</span>
        </div>
      </Reveal>
      {rows.map((t, r) => {
        const team = W.first[t];
        const y = 400 + r * 140;
        return (
          <div key={t}>
            <Reveal delay={0.2 + r * 0.15} x={-20} y={0} style={{ position: "absolute", left: 110, top: y - 22 }}>
              <TierPill tier={t} size={22} />
            </Reveal>
            <svg width="1360" height="60" style={{ position: "absolute", left: 420, top: y - 30, overflow: "visible" }}>
              {Array.from({ length: W.n }, (_, k) => {
                const filled = k < team;
                const on = pick.active === `${t}-${k}`;
                return (
                  <g key={k}>
                    <motion.circle cx={20 + k * 43} cy={30} r={16}
                      fill={filled ? TIER_COLOR[t] : "transparent"} stroke={on ? C.gold : filled ? TIER_COLOR[t] : C.cream} strokeWidth={on ? 5 : 3}
                      initial={{ scale: 0, opacity: 0 }} animate={{ scale: on ? 1.3 : 1, opacity: 1 }}
                      transition={{ delay: on ? 0 : 0.5 + r * 0.3 + k * 0.03, type: "spring", stiffness: 300, damping: 15 }} />
                    <circle cx={20 + k * 43} cy={30} r={21} fill="transparent" className="tap" {...pick.bind(`${t}-${k}`)} />
                  </g>
                );
              })}
            </svg>
            <Reveal delay={1.4 + r * 0.3} x={-10} y={0} style={{ position: "absolute", left: 1730, top: y - 34 }}>
              <span className="font-display" style={{ fontSize: 60, lineHeight: 1 }}>{team}<span style={{ fontSize: 32, color: C.muted }}>/30</span></span>
            </Reveal>
          </div>
        );
      })}
      {rows.map((t, r) =>
        R.we_examples[t].map((ex, k) => {
          const cx = 440 + k * 43, y = 400 + r * 140;
          return (
            <Tip key={`${t}-${k}`} show={pick.active === `${t}-${k}`} x={Math.min(Math.max(cx - 350, 110), 1110)}
              y={r < 2 ? y + 34 : y - 34} anchor={r < 2 ? "left" : "above-left"} width={700} accent={TIER_COLOR[t]}>
              <div style={{ fontSize: 23, lineHeight: 1.4 }}>
                &ldquo;{ex.tokens.map((tk, j) => tk.k === "target"
                  ? <b key={j} style={{ color: C.we, background: "rgba(79,201,224,0.2)", borderRadius: 6, padding: "0 4px" }}>{tk.t}</b>
                  : <span key={j} style={{ color: tk.k === "we" ? C.we : undefined }}>{tk.t}</span>)}&rdquo;
              </div>
              <div style={{ fontSize: 19, color: C.muted, marginTop: 8 }}>
                {ex.person} · {ex.season} playoffs · coded as <b style={{ color: C.cream }}>{REFERENT[ex.referent]}</b>
                {ex.referent !== "team" && ex.note ? ` (${ex.note})` : ""}
              </div>
            </Tip>
          );
        }))}
      <Reveal show={step >= 1} style={{ position: "absolute", left: 110, top: 790, width: 1700 }}>
        <Card style={{ padding: "26px 36px", display: "flex", gap: 50, alignItems: "center" }} glow={C.gold}>
          <div className="font-display" style={{ fontSize: 120, lineHeight: 0.9, color: C.gold }}>
            <CountUp to={W.agreement_pct} show={step >= 1} suffix="%" />
          </div>
          <div style={{ fontSize: 28, lineHeight: 1.45 }}>
            <b>Coded twice, once blind to the tier:</b> the codings agreed on {W.agreement_pct}% of uses (κ = {W.kappa}). Both coders were AI models.
            <br />
            <span style={{ color: C.gold, fontWeight: 700 }}>
              → BERT “we” classifier below the majority baseline (acc {R.bert_explain.we.accuracy.toFixed(2)} vs {R.bert_explain.we.baseline.toFixed(2)}):
              every “we” counts as team
            </span>
          </div>
        </Card>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ 8. Comparing like with like */
const CONF = [
  { label: "Won or lost", x: 560, y: 360 }, { label: "Points & minutes", x: 960, y: 360 }, { label: "Playoff round", x: 1360, y: 360 },
  { label: "Reporter's wording (“you”)", x: 560, y: 800 }, { label: "Question topics (LDA)", x: 960, y: 800 },
  { label: "Game day or other day", x: 1360, y: 800 },
];

const SIT = Object.fromEntries(R.bert_main.situation.map((x) => [x.effect, x]));
const eff = (k: string) => {
  const d = SIT[k];
  return <><b style={{ color: C.gold }}>{pp(d.diff)} points</b> of team-focused share [{pp(d.lo)}, {pp(d.hi)}]</>;
};
const TOPIC_IP = R.topics.find((t) => t.label === "Individual performance")!;
const gdShare = (t: Tier) => Math.round((100 * R.sample.tiers[t].game_day) / R.sample.tiers[t].units);
// what each control does in the main model (pill order as in CONF)
const CONF_INFO = [
  <>After a win (vs a loss): {eff("Won vs lost (game days)")}.</>,
  <>Scoring 10 more points: {eff("+10 points scored (game days)")}.</>,
  <>Conference finals (vs NBA Finals): {eff("Conference finals vs NBA Finals")}. {Math.round(R.finals_share.role * 100)}% of role-player units are at the Finals, {Math.round(R.finals_share.superstar * 100)}% of superstar units.</>,
  <>+10 “you” per 1,000 question words: {eff("+10 'you' per 1,000 question words")}. A “you” question invites an “I” answer.</>,
  <>10 topics found in the reporters&apos; questions (LDA). “Individual performance” is {(TOPIC_IP.superstar * 100).toFixed(1)}% of superstars&apos; questions, {(TOPIC_IP.role * 100).toFixed(1)}% of role players&apos;.</>,
  <>Units on a game day: superstars {gdShare("superstar")}%, role players {gdShare("role")}%.</>,
];

export function LikeWithLike({ step }: SlideProps) {
  const A = { x: 420, y: 580 }, B = { x: 1500, y: 580 };
  const NW = 470; // node width: "Team-focused share" must fit on one line
  const pick = usePick<number>(); // hover or click a control to see what it does
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Method" title="Comparing like with like" />
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0 }}>
        {CONF.map((c, k) => (
          <g key={k}>
            {[A, B].map((n, j) => (
              <motion.path key={j} d={`M${c.x} ${c.y + (c.y < 580 ? 37 : -37)} L${n.x + (j ? -190 : 190) * 0} ${n.y + (c.y < 580 ? -60 : 60)}`}
                stroke={step >= 2 ? C.dim : C.muted} strokeOpacity={step >= 2 ? 0.25 : 0.6} strokeWidth={3} strokeDasharray="8 9" fill="none"
                initial={{ pathLength: 0 }} animate={{ pathLength: step >= 1 ? 1 : 0 }} transition={{ duration: 0.6, delay: step >= 1 ? 0.3 + k * 0.08 : 0 }} />
            ))}
          </g>
        ))}
        <motion.path d={`M${A.x + NW / 2} 580 L${B.x - NW / 2 - 15} 580`} stroke={C.gold} strokeWidth={8} fill="none"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.6, duration: 0.8 }} />
        <motion.path d={`M${B.x - NW / 2 - 40} 560 L${B.x - NW / 2 - 10} 580 L${B.x - NW / 2 - 40} 600`} stroke={C.gold} strokeWidth={8} fill="none"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.3 }} />
      </svg>
      {[{ ...A, label: "Status tier", sub: "role · starter · superstar" }, { ...B, label: "Team-focused share", sub: "“I” and “we” read in context" }].map((n, k) => (
        <Reveal key={k} delay={0.3 + k * 0.2} scale={0.85} y={0} style={{ position: "absolute", left: n.x - NW / 2, top: n.y - 70, width: NW }}>
          <Card style={{ height: 140, display: "grid", placeItems: "center", textAlign: "center" }} glow={C.gold}>
            <div>
              <div className="font-display" style={{ fontSize: 52, lineHeight: 1, whiteSpace: "nowrap" }}>{n.label}</div>
              <div style={{ fontSize: 22, color: C.muted, marginTop: 8 }}>{n.sub}</div>
            </div>
          </Card>
        </Reveal>
      ))}
      <Reveal delay={1.2} scale={0.6} y={0} style={{ position: "absolute", left: 940, top: 488 }}>
        <span className="font-display" style={{ fontSize: 64, color: C.gold }}>?</span>
      </Reveal>
      {CONF.map((c, k) => (
        <Reveal key={k} show={step >= 1} delay={0.1 + k * 0.08} scale={0.7} y={0} style={{ position: "absolute", left: c.x - 185, top: c.y - 37, width: 370 }}>
          <div className="tap" {...pick.bind(k)} style={{
            height: 74, borderRadius: 37, display: "grid", placeItems: "center", fontSize: 26, fontWeight: 600,
            background: step >= 2 ? "#2b2117" : "rgba(36,27,20,0.95)",
            border: `2.5px solid ${step >= 2 || pick.active === k ? C.gold : "rgba(246,239,228,0.3)"}`, transition: "all .5s",
          }}>
            {c.label}
          </div>
          {step >= 2 && (
            <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2 + k * 0.06, type: "spring", stiffness: 300 }}
              className="font-cond"
              style={{ position: "absolute", top: -15, left: 125, width: 120, textAlign: "center", fontSize: 17, fontWeight: 700,
                letterSpacing: "0.12em", color: C.ink, background: C.gold, borderRadius: 999, padding: "2px 0" }}>
              CONTROL
            </motion.span>
          )}
        </Reveal>
      ))}
      {CONF.map((c, k) => (
        <Tip key={k} show={step >= 1 && pick.active === k} x={c.x} y={c.y < 580 ? c.y + 50 : c.y - 50} anchor={c.y < 580 ? "center" : "above"} width={440}>
          <div style={{ fontSize: 23 }}>{CONF_INFO[k]}</div>
          <div style={{ fontSize: 17, color: C.muted, marginTop: 6 }}>{k < 4 ? "Effect in the main model (all controls), 95% CI" : "How the tiers differ (raw shares)"}</div>
        </Tip>
      ))}
      <Reveal show={step >= 2} delay={0.3} style={{ position: "absolute", left: 110, top: 888, width: 1700, display: "flex", gap: 24 }}>
        <div style={{ flex: 1.25, fontSize: 22, lineHeight: 1.35, padding: "14px 22px", background: "rgba(28,21,16,0.88)", borderRadius: 14, borderLeft: `5px solid ${C.gold}` }}>
          <b>Binomial GLM (logit):</b> team-focused of self + team pronouns per unit · six controls · SEs clustered by player
        </div>
        <div style={{ flex: 1.25, fontSize: 22, lineHeight: 1.35, padding: "14px 22px", background: "rgba(28,21,16,0.88)", borderRadius: 14, borderLeft: `5px solid ${C.gold}` }}>
          <b>LDA (K = 10):</b> topic shares of the reporters&apos; questions, one document per unit · how: next slide
        </div>
        <div style={{ flex: 0.75, fontSize: 22, lineHeight: 1.35, padding: "14px 22px", background: "rgba(28,21,16,0.88)", borderRadius: 14, borderLeft: `5px solid ${C.gold}` }}>
          <b>Player fixed effects:</b> within-player, from {R.sample.tier_changers} tier changers
        </div>
      </Reveal>
    </div>
  );
}

/* ------------------------------------------------------------------ LDA on the reporters' questions (Step 22): one document, start to end */
const LM = R.lda_method;
type Tok = { t: string; why?: string; term?: string; topic?: number; p?: number; gap?: boolean };
// colours of the example's three topics; validated (dataviz validator, dark mode, on the card and the floor): all checks pass
const TOPIC_COL: Record<number, string> = { 4: "#c08518", 1: "#dc6386", 9: "#76a234" };
const OTHER_TOPIC = "#6f604f";
const topicCol = (k?: number) => (k && TOPIC_COL[k]) || OTHER_TOPIC;
const TNAME = LM.topic_names as Record<string, string>;
const WHY: Record<string, string> = {
  "stop word": "stop word", "under 3 letters": "under 3 letters", "spoken filler": "spoken filler",
  "name word": "name word (capitalised mid-sentence in > 50% of uses)", contraction: "contraction",
  min_df: "in fewer than 10 documents (min_df)", max_df: "in more than half of the documents (max_df)", "generic word": "generic word",
};
const WHY_SHORT: Record<string, string> = {
  "stop word": "stop words", "under 3 letters": "under 3 letters", "spoken filler": "filler", "name word": "names",
  contraction: "contractions", min_df: "min_df", max_df: "max_df", "generic word": "generic",
};
const KX = (j: number) => 26 + j * 54;                 // K position inside a mini chart (6 values)
const NPMI_Y = lin(0.1, 0.14, 118, 52);
const STAB_Y = lin(0.6, 0.85, 118, 52);
const MINI = [{ key: "npmi" as const, title: "NPMI coherence", y: NPMI_Y, x0: 0, fmt: (v: number) => v.toFixed(3) },
  { key: "stability" as const, title: "seed stability", y: STAB_Y, x0: 350, fmt: (v: number) => v.toFixed(2) }];
const LAB = { fontSize: 20, letterSpacing: "0.14em", color: C.gold, fontWeight: 700 } as const;

export function LdaMethod({ step }: SlideProps) {
  const word = usePick<number>();   // hover or click a word of the questions
  const kp = usePick<number>();     // hover or click a K in the sweep
  const ex = LM.example;
  const toks = ex.tokens as unknown as Tok[];
  const removed = Object.entries(toks.reduce<Record<string, number>>((m, t) => {
    if (t.why && t.why !== "kept") m[t.why] = (m[t.why] ?? 0) + 1;
    return m;
  }, {})).sort((x, y) => y[1] - x[1]);
  const w = word.active !== null ? toks[word.active] : null;
  const c = LM.corpus;
  const theta = ex.theta;
  const shown = theta.filter((d) => TOPIC_COL[d.topic]);
  const rest = 1 - shown.reduce((s, d) => s + d.share, 0);
  const sw = LM.sweep;
  const ki = kp.active;
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Method · question topics · latent Dirichlet allocation (scikit-learn 1.8, batch variational Bayes)"
        title="LDA turns each unit's questions into ten topic shares" size={80} />

      {/* left: one document, word by word */}
      <Reveal delay={0.2} style={{ position: "absolute", left: 110, top: 300, width: 930 }}>
        <Card style={{ height: 562, padding: "22px 32px", position: "relative" }}>
          <div style={{ display: "flex", gap: 18, alignItems: "center" }}>
            <Headshot id={P.lebron.id} size={70} ring={TIER_COLOR.superstar} />
            <div>
              <div style={{ fontSize: 26, fontWeight: 700 }}>One document: {ex.person}, {ex.season} conference finals, Game 6</div>
              <div style={{ fontSize: 20, color: C.muted }}>every question to one player in one press conference · {ex.n_questions} questions (4 shown)</div>
            </div>
          </div>
          <p style={{ fontSize: 27, lineHeight: 1.6, margin: "16px 0 0", color: C.dim }}>
            {toks.map((t, j) => {
              if (!t.why) return <span key={j} style={{ color: t.gap ? C.muted : C.dim }}>{t.t}</span>;
              const kept = t.why === "kept";
              const col = step >= 1 && kept ? topicCol(t.topic) : C.cream;
              const on = word.active === j;
              return (
                <motion.span key={j} className="tap" {...word.bind(j)} initial={false}
                  animate={kept
                    ? { backgroundColor: step >= 1 ? a(col, 0.3) : "rgba(0,0,0,0)", boxShadow: `inset 0 -3px 0 ${step >= 1 ? col : a(C.cream, 0.45)}` }
                    : { backgroundColor: "rgba(0,0,0,0)", boxShadow: "inset 0 0px 0 rgba(0,0,0,0)" }}
                  transition={{ duration: 0.4, delay: step >= 1 && kept ? 0.1 + (j % 40) * 0.012 : 0 }}
                  style={{ color: kept ? C.cream : C.dim, fontWeight: kept ? 700 : 400, borderRadius: 6, padding: "0 2px",
                    outline: on ? `2px solid ${C.gold}` : "none" }}>
                  {t.t}
                </motion.span>
              );
            })}
          </p>
          <div style={{ position: "absolute", left: 32, right: 32, bottom: 18, fontSize: 21, lineHeight: 1.35, color: C.muted, borderTop: `1px solid ${C.grid}`, paddingTop: 10, minHeight: 64 }}>
            {w && w.why === "kept" ? (
              <>“{w.t}” → term <b style={{ color: C.cream }}>{w.term}</b>{step >= 1 && w.topic
                ? <> · most likely topic here: <b style={{ color: C.cream }}>{TNAME[String(w.topic)]}</b>, {Math.round((w.p ?? 0) * 100)}% (θ<sub>dk</sub>·φ<sub>kw</sub>, normalised over k)</>
                : " · kept"}</>
            ) : w ? (
              <>“{w.t}” removed: {WHY[w.why ?? ""]}</>
            ) : (
              <>Bold = kept term. Removed here: {removed.map(([k, n]) => `${n} ${WHY_SHORT[k] ?? k}`).join(" · ")}</>
            )}
          </div>
        </Card>
      </Reveal>
      <Reveal delay={0.6} style={{ position: "absolute", left: 110, top: 880, width: 930, display: "flex", flexWrap: "wrap", gap: 10 }}>
        {["lowercase, ≥ 3 letters", "stop words + spoken filler", `${c.names_removed} name words`, "plurals → singular", "1- and 2-grams", "min_df 10 · max_df 0.5"].map((x) => (
          <span key={x} style={{ fontSize: 21, padding: "5px 14px", borderRadius: 999, border: `1.5px solid ${a(C.cream, 0.25)}`, color: C.cream }}>{x}</span>
        ))}
        <span style={{ fontSize: 21, padding: "5px 14px", borderRadius: 999, background: C.gold, color: C.ink, fontWeight: 700 }}>= {c.terms.toLocaleString()} terms</span>
      </Reveal>

      {/* right top: the count vector */}
      <Reveal delay={0.5} style={{ position: "absolute", left: 1080, top: 300, width: 730 }}>
        <Card style={{ height: 190, padding: "16px 28px" }}>
          <div className="font-cond" style={LAB}>COUNT VECTOR OF THIS DOCUMENT</div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
            <span className="font-display" style={{ fontSize: 46, color: C.cream }}>{ex.kept}</span>
            <span style={{ fontSize: 22 }}>term tokens · {ex.distinct} of {c.terms.toLocaleString()} terms</span>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 }}>
            {ex.terms.map((t) => (
              <span key={t.term} style={{ fontSize: 20, padding: "2px 12px", borderRadius: 8, background: C.surface2 }}>{t.term} <b style={{ color: C.gold }}>{t.n}</b></span>
            ))}
          </div>
          <div style={{ fontSize: 18, color: C.dim, marginTop: 8 }}>
            matrix {c.docs.toLocaleString()} × {c.terms.toLocaleString()} · raw counts, not tf-idf · {(c.nonzero_share * 100).toFixed(1)}% non-zero
          </div>
        </Card>
      </Reveal>

      {/* right middle: LDA and theta */}
      <Reveal show={step >= 1} delay={0.2} style={{ position: "absolute", left: 1080, top: 500, width: 730 }}>
        <Card style={{ height: 230, padding: "16px 28px" }} glow={step === 1 ? C.gold : undefined}>
          <div className="font-cond" style={LAB}>LDA, K = {LM.k} → θ OF THIS DOCUMENT</div>
          <svg width={674} height={40} style={{ display: "block", marginTop: 8 }}>
            {(() => {
              let x0 = 0;
              const segs = [...shown.map((d) => ({ k: d.topic, v: d.share })), { k: 0, v: rest }];
              return segs.map((sg) => {
                const wd = sg.v * 674;
                const r = <motion.rect key={sg.k} x={x0} y={0} height={40} rx={4} fill={sg.k ? topicCol(sg.k) : OTHER_TOPIC}
                  initial={{ width: 0 }} animate={{ width: Math.max(0, wd - 2) }} transition={{ delay: 0.4, duration: 0.7, ease }} />;
                x0 += wd;
                return r;
              });
            })()}
          </svg>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 22px", marginTop: 8, fontSize: 21 }}>
            {shown.map((d) => (
              <span key={d.topic} style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
                <span style={{ width: 16, height: 16, borderRadius: 4, background: topicCol(d.topic) }} />
                {d.name} <b>{Math.round(d.share * 100)}%</b>
              </span>
            ))}
            <span style={{ color: C.muted }}>7 others {Math.round(rest * 100)}%</span>
          </div>
          <div style={{ fontSize: 19, color: C.muted, marginTop: 8, lineHeight: 1.35 }}>
            α = η = 1/K · batch variational Bayes, 50 iterations · seed 0<br />
            θ ({c.docs.toLocaleString()} × {LM.k}) → controls in the GLM, topic 1 = baseline
          </div>
        </Card>
      </Reveal>

      {/* right bottom: choosing K */}
      <Reveal show={step >= 2} delay={0.2} style={{ position: "absolute", left: 1080, top: 742, width: 730 }}>
        <Card style={{ height: 262, padding: "14px 28px" }} glow={step === 2 ? C.gold : undefined}>
          <div className="font-cond" style={LAB}>CHOOSING K: {sw.map((d) => d.K).join(", ")} · 3 SEEDS EACH</div>
          <svg width={674} height={150} style={{ display: "block" }}>
            {MINI.map((m) => (
              <g key={m.key} transform={`translate(${m.x0}, 0)`}>
                <text x={0} y={20} fontSize={19} fill={C.muted}>{m.title}</text>
                <polyline points={sw.map((d, j) => `${KX(j)},${m.y(d[m.key])}`).join(" ")} fill="none" stroke={C.dim} strokeWidth={2} />
                {sw.map((d, j) => {
                  const sel = d.K === LM.k, on = ki === d.K;
                  return (
                    <g key={d.K}>
                      <circle cx={KX(j)} cy={m.y(d[m.key])} r={sel ? 9 : 7} fill={sel ? C.gold : C.muted} stroke={C.surface} strokeWidth={2} />
                      {(sel || on) && <text x={KX(j)} y={m.y(d[m.key]) - 14} textAnchor="middle" fontSize={18} fill={C.cream} fontWeight={700}>{m.fmt(d[m.key])}</text>}
                      <text x={KX(j)} y={144} textAnchor="middle" fontSize={18} fill={sel ? C.gold : C.muted} fontWeight={sel ? 700 : 400}>{d.K}</text>
                      <rect x={KX(j) - 26} y={30} width={52} height={120} fill="transparent" className="tap" {...kp.bind(d.K)} />
                    </g>
                  );
                })}
              </g>
            ))}
          </svg>
          <div style={{ fontSize: 19, color: C.muted, lineHeight: 1.35 }}>
            K = 5 scores higher but merges legacy with season · K = 10: highest NPMI of 8–15, every topic nameable · α 0.5 or 1: same themes · K = 5 rerun as a check
          </div>
        </Card>
      </Reveal>
      {sw.map((d) => (
        <Tip key={d.K} show={step >= 2 && ki === d.K} x={1445} y={782} anchor="above" width={560}>
          <b>K = {d.K}</b>: NPMI {d.npmi.toFixed(3)} · diversity {d.diversity.toFixed(2)} · stability {d.stability.toFixed(2)}
          <div style={{ fontSize: 17, color: C.muted, marginTop: 4 }}>NPMI: top-10 words, document co-occurrence · stability: topics matched across seeds (Hungarian, cosine)</div>
        </Tip>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ 9. Three lenses on the words */
function LensIcon({ k }: { k: number }) {
  const d = { initial: { pathLength: 0 }, animate: { pathLength: 1 }, transition: { duration: 1, delay: 0.4 } };
  if (k === 0)
    return (
      <svg width="150" height="110">
        {[[40, 60, 34], [95, 42, 26], [110, 85, 18], [62, 22, 14]].map(([x, y, r], j) => (
          <motion.circle key={j} cx={x} cy={y} r={r} fill={[C.gold, C.muted, C.we, C.cream][j] + "55"} stroke={[C.gold, C.muted, C.we, C.cream][j]} strokeWidth={3}
            initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.5 + j * 0.1, type: "spring" }} />
        ))}
      </svg>
    );
  if (k === 1)
    return (
      <svg width="150" height="110">
        <line x1="75" y1="5" x2="75" y2="105" stroke={C.cream} strokeOpacity="0.5" strokeWidth="2" />
        {[[60, 18], [45, 44], [30, 70], [50, 96]].map(([w, y], j) => (
          <motion.rect key={`l${j}`} x={75 - w} y={y - 9} width={w} height={16} rx={4} fill={TIER_COLOR.role}
            initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} style={{ originX: 1 }} transition={{ delay: 0.5 + j * 0.08 }} />
        ))}
        {[[66, 18], [50, 44], [36, 70], [24, 96]].map(([w, y], j) => (
          <motion.rect key={`r${j}`} x={75} y={y - 9} width={w} height={16} rx={4} fill={TIER_COLOR.superstar}
            initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} style={{ originX: 0 }} transition={{ delay: 0.5 + j * 0.08 }} />
        ))}
      </svg>
    );
  return (
    <svg width="150" height="110">
      <rect x="20" y="5" width="100" height="100" fill="none" stroke={C.cream} strokeOpacity="0.4" strokeWidth="2" />
      <line x1="20" y1="105" x2="120" y2="5" stroke={C.cream} strokeOpacity="0.4" strokeDasharray="5 5" strokeWidth="2" />
      <motion.path d="M20 105 C 30 50, 60 25, 120 5" fill="none" stroke={C.gold} strokeWidth="5" {...d} />
    </svg>
  );
}

const LENSES = [
  { name: "Topic model (LDA)", q: "What do reporters ask about?",
    how: "10 topics from the reporters' questions, picked by coherence and stability.", use: "Controls in the regression · compared by tier" },
  { name: "Fightin' Words", q: "Which words separate the tiers?",
    how: "Log-odds with an informative prior (Monroe et al., 2008); names, teams and cities removed; re-checked one player at a time.", use: "Describes what differs" },
  { name: "Classifiers", q: "Can the words predict the tier? Do “I” and “we” help?",
    how: "Logistic regression on word counts or sentence embeddings (MiniLM); 5-fold, split by player; scored with AUC.", use: "Is the difference in the pronouns?" },
];

export function Lenses({ step }: SlideProps) {
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      <Header kicker="Method · beyond pronouns" title="Three more ways to look at the words" />
      {LENSES.map((l, k) => (
        <Reveal key={k} show={step >= k} y={50} style={{ position: "absolute", left: 110 + k * 580, top: 300, width: 540 }}>
          <Card style={{ height: 580, padding: "34px 36px" }} glow={step === k ? C.gold : undefined}>
            <LensIcon k={k} />
            <div className="font-display" style={{ fontSize: 58, lineHeight: 1, marginTop: 18 }}>{l.name}</div>
            <div style={{ fontSize: 31, fontWeight: 600, lineHeight: 1.25, marginTop: 16, color: C.gold }}>{l.q}</div>
            <div style={{ fontSize: 25, color: C.muted, lineHeight: 1.4, marginTop: 18 }}>{l.how}</div>
            <div className="font-cond" style={{ fontSize: 21, letterSpacing: "0.12em", fontWeight: 700, marginTop: 22, color: C.cream, textTransform: "uppercase" }}>
              → {l.use}
            </div>
          </Card>
        </Reveal>
      ))}
    </div>
  );
}
