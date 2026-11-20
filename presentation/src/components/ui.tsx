"use client";

import { animate, AnimatePresence, motion } from "framer-motion";
import { CSSProperties, MouseEvent, ReactNode, useEffect, useState } from "react";
import { a, C, ease, Tier, TIER_COLOR, TIER_NAME } from "@/lib/theme";

/** Fades/slides in when `show` turns true, back out when it turns false (so stepping backwards works). */
export function Reveal({
  show = true, children, delay = 0, y = 26, x = 0, scale = 1, style, className,
}: {
  show?: boolean; children: ReactNode; delay?: number; y?: number; x?: number; scale?: number;
  style?: CSSProperties; className?: string;
}) {
  const hidden = { opacity: 0, y, x, scale, filter: "blur(8px)" };
  return (
    <motion.div
      className={className}
      style={{ ...style, pointerEvents: show ? style?.pointerEvents : "none" }}
      initial={hidden}
      animate={show ? { opacity: 1, y: 0, x: 0, scale: 1, filter: "blur(0px)" } : hidden}
      transition={{ duration: 0.65, delay: show ? delay : 0, ease }}
    >
      {children}
    </motion.div>
  );
}

export function CountUp({
  to, show = true, decimals = 0, duration = 1.5, delay = 0, prefix = "", suffix = "",
}: {
  to: number; show?: boolean; decimals?: number; duration?: number; delay?: number; prefix?: string; suffix?: string;
}) {
  const [v, setV] = useState(0);
  useEffect(() => {
    if (!show) return;
    const c = animate(0, to, { duration, delay, ease: [0.16, 1, 0.3, 1], onUpdate: setV });
    return () => c.stop();
  }, [show, to, duration, delay]);
  const shown = show ? v : 0;
  return (
    <span className="tabular">
      {prefix}
      {shown.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}
      {suffix}
    </span>
  );
}

/** Slide title: each word rises out of a mask. */
export function Title({ text, size = 92, delay = 0.1, style }: { text: string; size?: number; delay?: number; style?: CSSProperties }) {
  return (
    <h1 className="font-display" style={{ fontSize: size, lineHeight: 0.98, margin: 0, color: C.cream, ...style }}>
      {text.split(" ").map((w, i) => (
        <span key={i} style={{ display: "inline-block", overflow: "hidden", verticalAlign: "top", paddingRight: "0.24em" }}>
          <motion.span
            style={{ display: "inline-block" }}
            initial={{ y: "105%" }}
            animate={{ y: "0%" }}
            transition={{ delay: delay + i * 0.045, duration: 0.7, ease }}
          >
            {w}
          </motion.span>
        </span>
      ))}
    </h1>
  );
}

export function Kicker({ children, color = C.gold, style }: { children: ReactNode; color?: string; style?: CSSProperties }) {
  return (
    <motion.div
      className="font-cond"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, ease }}
      style={{ fontSize: 24, fontWeight: 700, letterSpacing: "0.22em", textTransform: "uppercase", color, ...style }}
    >
      {children}
    </motion.div>
  );
}

/** Standard slide header: kicker + title at the top left. */
export function Header({ kicker, title, size = 88, width = 1700 }: { kicker: string; title: string; size?: number; width?: number }) {
  return (
    <div style={{ position: "absolute", left: 110, top: 118, width }}>
      <Kicker>{kicker}</Kicker>
      <div style={{ height: 10 }} />
      <Title text={title} size={size} />
    </div>
  );
}

export function Ball({ size = 60, style, spin = false }: { size?: number; style?: CSSProperties; spin?: boolean }) {
  const svg = (
    <svg width={size} height={size} viewBox="-52 -52 104 104" style={{ display: "block" }}>
      <defs>
        <radialGradient id="ballg" cx="-0.25" cy="-0.3" r="1.1">
          <stop offset="0%" stopColor="#ffb36b" />
          <stop offset="55%" stopColor={C.ball} />
          <stop offset="100%" stopColor="#b8480f" />
        </radialGradient>
      </defs>
      <circle r="50" fill="url(#ballg)" stroke="#2a1408" strokeWidth="3" />
      <g fill="none" stroke="#2a1408" strokeWidth="3.2" strokeLinecap="round">
        <path d="M0 -50 V50" />
        <path d="M-50 0 H50" />
        <path d="M-35 -36 C-15 -15 -15 15 -35 36" />
        <path d="M35 -36 C15 -15 15 15 35 36" />
      </g>
    </svg>
  );
  if (!spin) return <div style={style}>{svg}</div>;
  return (
    <motion.div style={style} animate={{ rotate: 360 }} transition={{ duration: 6, repeat: Infinity, ease: "linear" }}>
      {svg}
    </motion.div>
  );
}

export function Headshot({
  id, size = 150, ring, style, grayscale = false,
}: { id: number; size?: number; ring?: string; style?: CSSProperties; grayscale?: boolean }) {
  return (
    <div
      style={{
        width: size, height: size, borderRadius: "50%", overflow: "hidden", flex: "none",
        background: `radial-gradient(circle at 50% 35%, ${C.surface2}, #0d0906)`,
        boxShadow: ring ? `0 0 0 ${Math.max(3, size / 28)}px ${ring}, 0 10px 30px rgba(0,0,0,0.45)` : "0 10px 30px rgba(0,0,0,0.45)",
        position: "relative", ...style,
      }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`/img/players/${id}.png`}
        alt=""
        style={{
          // maxWidth/height override Tailwind's preflight (img { max-width: 100%; height: auto }), which shrank the
          // image to the circle's width: faces sat left of centre and the shoulders stopped at a hard edge
          position: "absolute", width: "140%", maxWidth: "none", height: "auto", left: "-20%", top: "6%",
          filter: grayscale ? "grayscale(1) brightness(0.8)" : undefined,
        }}
      />
    </div>
  );
}

export function TierPill({ tier, size = 22, style }: { tier: Tier; size?: number; style?: CSSProperties }) {
  return (
    <span
      className="font-cond"
      style={{
        display: "inline-flex", alignItems: "center", gap: 8, padding: `${size * 0.18}px ${size * 0.6}px`,
        borderRadius: 999, border: `2px solid ${TIER_COLOR[tier]}`, color: C.cream, fontSize: size,
        fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", background: "rgba(18,12,8,0.72)", ...style,
      }}
    >
      <span style={{ width: size * 0.5, height: size * 0.5, borderRadius: "50%", background: TIER_COLOR[tier] }} />
      {TIER_NAME[tier]}
    </span>
  );
}

export function Card({ children, style, glow }: { children: ReactNode; style?: CSSProperties; glow?: string }) {
  return (
    <div
      style={{
        background: "linear-gradient(160deg, rgba(40,30,22,0.95), rgba(22,16,12,0.95))",
        border: `1.5px solid ${glow ?? "rgba(246,239,228,0.12)"}`,
        borderRadius: 26,
        boxShadow: `${glow ? `0 0 44px ${a(glow, 0.28)}, ` : ""}0 22px 50px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

/** A quote with "I" and "we" words marked; marks light up when iOn / weOn. */
export function Quote({
  tokens, iOn, weOn, size = 40, style,
}: { tokens: { t: string; k: string }[]; iOn: boolean; weOn: boolean; size?: number; style?: CSSProperties }) {
  let n = 0;
  return (
    <p style={{ fontSize: size, lineHeight: 1.42, margin: 0, color: C.cream, fontWeight: 500, ...style }}>
      {tokens.map((tk, idx) => {
        if (!tk.k) return <span key={idx}>{tk.t}</span>;
        const on = tk.k === "i" ? iOn : weOn;
        const col = tk.k === "i" ? C.i : C.we;
        const order = n++;
        return (
          <motion.span
            key={idx}
            initial={false}
            animate={on
              ? { backgroundColor: `${col}33`, color: col, boxShadow: `inset 0 -4px 0 ${col}` }
              : { backgroundColor: "rgba(0,0,0,0)", color: C.cream, boxShadow: "inset 0 0px 0 rgba(0,0,0,0)" }}
            transition={{ duration: 0.4, delay: on ? 0.15 + order * 0.12 : 0 }}
            style={{ borderRadius: 8, padding: "0 4px", fontWeight: 700 }}
          >
            {tk.t}
          </motion.span>
        );
      })}
    </p>
  );
}

export function Legend({ items, style }: { items: { label: string; color: string; hollow?: boolean }[]; style?: CSSProperties }) {
  return (
    <div style={{ display: "flex", gap: 30, fontSize: 24, color: C.muted, alignItems: "center", ...style }}>
      {items.map((it) => (
        <span key={it.label} style={{ display: "inline-flex", gap: 10, alignItems: "center" }}>
          <span
            style={{
              width: 18, height: 18, borderRadius: "50%",
              background: it.hollow ? "transparent" : it.color, border: `3px solid ${it.color}`,
            }}
          />
          {it.label}
        </span>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ interaction */

/** Click handler that does not let the click reach the deck (which would move to the next build). */
export const stop = (fn: () => void) => (e: MouseEvent) => {
  e.stopPropagation();
  fn();
};

/** A clickable area: runs onTap and keeps the deck where it is. */
export function Tap({
  onTap, children, style, className = "tap", title,
}: { onTap: () => void; children: ReactNode; style?: CSSProperties; className?: string; title?: string }) {
  return (
    <div className={className} title={title} style={style} onClick={stop(onTap)}>
      {children}
    </div>
  );
}

/** Hover to show; click to pin (the click stays on the slide). */
export function usePick<K extends string | number>() {
  const [hov, setHov] = useState<K | null>(null);
  const [pin, setPin] = useState<K | null>(null);
  const active = hov ?? pin;
  const bind = (k: K) => ({
    onMouseEnter: () => setHov(k),
    onMouseLeave: () => setHov((h) => (h === k ? null : h)),
    onClick: stop(() => setPin((p) => (p === k ? null : k))),
  });
  /** hover only: clicks still move the deck on */
  const hover = (k: K) => ({
    onMouseEnter: () => setHov(k),
    onMouseLeave: () => setHov((h) => (h === k ? null : h)),
  });
  return { active, bind, hover };
}

/** Tooltip in stage pixels (1920 x 1080). anchor: which point of the box sits at (x, y). */
export function Tip({
  show, x, y, children, anchor = "left", width, accent = C.gold,
}: {
  show: boolean; x: number; y: number; children: ReactNode; anchor?: "left" | "right" | "center" | "above" | "above-right" | "above-left";
  width?: number; accent?: string;
}) {
  const tx = anchor === "right" || anchor === "above-right" ? "-100%" : anchor === "center" || anchor === "above" ? "-50%" : "0";
  const ty = anchor.startsWith("above") ? "-100%" : "0";
  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `translate(${tx}, ${ty})`, zIndex: 30, pointerEvents: "none" }}>
      <AnimatePresence>
        {show && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.98 }}
            transition={{ duration: 0.18 }}
            style={{
              background: "rgba(12,9,7,0.97)", border: `1.5px solid ${accent}`, borderRadius: 14, padding: "12px 18px",
              fontSize: 22, lineHeight: 1.35, color: C.cream, width, whiteSpace: width ? "normal" : "nowrap",
              boxShadow: `0 14px 34px rgba(0,0,0,0.6), 0 0 24px ${a(accent, 0.18)}`,
            }}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
