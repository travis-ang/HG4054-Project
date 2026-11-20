"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Ball } from "@/components/ui";
import { a, C, ease } from "@/lib/theme";
import { QUARTER, SlideDef } from "@/slides/types";

// dot-matrix look behind LED digits
const LED_BG = "radial-gradient(circle, rgba(255,255,255,0.045) 1px, transparent 1.6px) 0 0 / 6px 6px, #070606";

const mmss = (s: number) => `${Math.floor(s / 60).toString().padStart(2, "0")}:${Math.floor(s % 60).toString().padStart(2, "0")}`;

/** Scoreboard header, court-line progress bar, quarter banner, optional rehearsal clock and notes. */
export default function Chrome({
  slides, i, s, banner, hud, notes, elapsed,
}: {
  slides: SlideDef[]; i: number; s: number; banner: number | null; hud: boolean; notes: boolean; elapsed: number;
}) {
  const slide = slides[i];
  const q = QUARTER[slide.quarter];
  const total = slides.reduce((a, b) => a + b.seconds, 0);
  const before = slides.slice(0, i).reduce((a, b) => a + b.seconds, 0);
  const x0 = 110, x1 = 1810;
  const frac = (before + (slide.seconds * (s + 1)) / slide.steps) / total;
  const qStarts = [1, 2, 3, 4].map((qq) => {
    const k = slides.findIndex((d) => d.quarter === qq);
    return { qq, f: slides.slice(0, k).reduce((a, b) => a + b.seconds, 0) / total };
  });

  return (
    <>
      {/* top left: talk name */}
      <div style={{ position: "absolute", left: 110, top: 40, display: "flex", alignItems: "center", gap: 14 }}>
        <Ball size={30} spin />
        <span className="font-cond" style={{ fontSize: 21, letterSpacing: "0.2em", color: C.muted, fontWeight: 600 }}>
          ARE SUPERSTARS MORE SELF-FOCUSED?
        </span>
      </div>

      {/* top right: arena scoreboard (quarter, period name, red shot-clock slide counter) */}
      <div
        style={{
          position: "absolute", right: 110, top: 24, display: "flex", alignItems: "stretch", height: 66,
          background: "linear-gradient(#1b1a19, #0a0908)", border: "2px solid #3d3a36", borderRadius: 10,
          boxShadow: "0 8px 24px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.08), inset 0 0 18px rgba(0,0,0,0.7)", overflow: "hidden",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "0 16px", minWidth: 72,
          background: LED_BG }}>
          <span className="font-cond" style={{ fontSize: 12, letterSpacing: "0.3em", color: C.muted, fontWeight: 700, lineHeight: 1 }}>QTR</span>
          <AnimatePresence mode="popLayout" initial={false}>
            <motion.span
              key={q.short}
              initial={{ y: -30, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 30, opacity: 0 }}
              transition={{ duration: 0.45, ease }}
              className="font-display"
              style={{ fontSize: 40, lineHeight: 1, color: C.led, textShadow: `0 0 12px ${a(C.led, 0.75)}` }}
            >
              {q.short}
            </motion.span>
          </AnimatePresence>
        </div>
        <div
          className="font-cond"
          style={{
            padding: "0 20px", display: "flex", alignItems: "center", fontSize: 22, fontWeight: 700, borderLeft: "2px solid #2e2b28",
            letterSpacing: "0.16em", textTransform: "uppercase", color: C.cream, minWidth: 220,
          }}
        >
          {q.label}
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "0 16px",
          borderLeft: "2px solid #2e2b28", background: LED_BG }}>
          <span className="font-cond" style={{ fontSize: 12, letterSpacing: "0.3em", color: C.muted, fontWeight: 700, lineHeight: 1 }}>SLIDE</span>
          <span className="font-display tabular" style={{ fontSize: 40, lineHeight: 1, color: C.ledRed, textShadow: `0 0 12px ${a(C.ledRed, 0.75)}` }}>
            {String(i + 1).padStart(2, "0")}
            <span style={{ color: a(C.ledRed, 0.4), margin: "0 5px" }}>/</span>
            {String(slides.length).padStart(2, "0")}
          </span>
        </div>
      </div>

      {/* bottom: sideline progress with the four quarters */}
      <svg width="1920" height="80" style={{ position: "absolute", left: 0, top: 1000 }}>
        <line x1={x0} x2={x1} y1={40} y2={40} stroke="rgba(246,239,228,0.2)" strokeWidth={4} strokeLinecap="round" />
        <motion.line
          x1={x0} y1={40} y2={40} stroke={C.gold} strokeWidth={4} strokeLinecap="round"
          initial={false} animate={{ x2: x0 + frac * (x1 - x0) }} transition={{ type: "spring", stiffness: 60, damping: 16 }}
        />
        {qStarts.map(({ qq, f }) => (
          <g key={qq} transform={`translate(${x0 + f * (x1 - x0)},0)`}>
            <line y1={30} y2={50} stroke="rgba(246,239,228,0.45)" strokeWidth={3} />
            <text y={22} x={6} fill={slide.quarter === qq ? C.gold : "rgba(246,239,228,0.5)"} fontSize={17}
              fontWeight={700} letterSpacing="0.12em" style={{ fontFamily: "var(--font-barlow-cond)" }}>
              {QUARTER[qq].short} · {QUARTER[qq].label.toUpperCase()}
            </text>
          </g>
        ))}
      </svg>
      <motion.div
        style={{ position: "absolute", top: 1027 }}
        initial={false}
        animate={{ left: x0 + frac * (x1 - x0) - 13, rotate: frac * 1440 }}
        transition={{ type: "spring", stiffness: 60, damping: 16 }}
      >
        <Ball size={26} />
      </motion.div>

      {/* quarter banner */}
      <AnimatePresence>
        {banner !== null && (
          <motion.div
            key={banner}
            initial={{ clipPath: "polygon(0 0, 0 0, -20% 100%, -20% 100%)" }}
            animate={{ clipPath: "polygon(0 0, 120% 0, 100% 100%, -20% 100%)" }}
            exit={{ clipPath: "polygon(120% 0, 120% 0, 100% 100%, 100% 100%)" }}
            transition={{ duration: 0.5, ease: [0.76, 0, 0.24, 1] }}
            style={{
              position: "absolute", inset: 0, zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center",
              background: "radial-gradient(circle, rgba(255,255,255,0.04) 1.2px, transparent 1.8px) 0 0 / 9px 9px, linear-gradient(115deg, #070505 0%, #1d130b 55%, #4a1d06 100%)",
            }}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.5, ease }}
              style={{ display: "flex", alignItems: "center", gap: 60 }}
            >
              <div className="font-display" style={{ fontSize: 330, color: C.led, lineHeight: 0.8, textShadow: `0 0 50px ${a(C.led, 0.55)}` }}>
                {QUARTER[banner].short}
              </div>
              <div>
                <div className="font-cond" style={{ fontSize: 34, letterSpacing: "0.3em", color: C.muted, fontWeight: 700 }}>
                  {QUARTER[banner].long.toUpperCase()}
                </div>
                <div className="font-display" style={{ fontSize: 140, color: C.cream, lineHeight: 0.95 }}>
                  {QUARTER[banner].label}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* rehearsal clock (press T) */}
      {hud && (
        <div
          className="font-display tabular"
          style={{
            position: "absolute", left: 860, top: 26, width: 200, textAlign: "center", fontSize: 40, color: C.led, textShadow: `0 0 10px ${a(C.led, 0.6)}`,
            background: LED_BG, border: "2px solid #3d3a36", borderRadius: 10, padding: "4px 0", zIndex: 40,
          }}
        >
          {mmss(elapsed)}
          <div style={{ fontSize: 20, color: C.muted }}>target {mmss(before + slide.seconds)}</div>
        </div>
      )}

      {/* rehearsal notes (press N) */}
      {notes && (
        <div
          style={{
            position: "absolute", left: 110, right: 110, bottom: 90, zIndex: 40, background: "rgba(10,7,5,0.94)",
            border: "1px solid rgba(246,239,228,0.2)", borderRadius: 16, padding: "18px 26px", fontSize: 26, color: C.cream,
          }}
        >
          {slide.notes.map((n, k) => <div key={k}>• {n}</div>)}
        </div>
      )}
    </>
  );
}
