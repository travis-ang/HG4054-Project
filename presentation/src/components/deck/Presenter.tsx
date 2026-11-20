"use client";

import { CSSProperties, useEffect, useRef, useState } from "react";
import { nextPos, prevPos, SLIDES } from "@/slides";
import { Pos, QUARTER } from "@/slides/types";

const CHANNEL = "hg4054-deck";
const mmss = (s: number) => `${s < 0 ? "−" : ""}${Math.floor(Math.abs(s) / 60)}:${Math.floor(Math.abs(s) % 60).toString().padStart(2, "0")}`;

/** Presenter view (open with P in the deck): prompts, timing and the next slide. Arrow keys work here too. */
export default function Presenter() {
  const [pos, setPos] = useState<Pos>({ i: 0, s: 0 });
  const [t0, setT0] = useState<number | null>(null);
  const [now, setNow] = useState(0);
  const ch = useRef<BroadcastChannel | null>(null);

  useEffect(() => {
    const c = new BroadcastChannel(CHANNEL);
    ch.current = c;
    c.onmessage = (e) => {
      if (e.data?.type === "pos") {
        setPos(e.data.pos);
        setT0(e.data.t0 ?? null);
      }
    };
    c.postMessage({ type: "hello" });
    const id = window.setInterval(() => setNow(Date.now()), 500);
    return () => { c.close(); window.clearInterval(id); };
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (["ArrowRight", " ", "PageDown"].includes(e.key)) ch.current?.postMessage({ type: "go", pos: nextPos(pos) });
      else if (["ArrowLeft", "PageUp"].includes(e.key)) ch.current?.postMessage({ type: "go", pos: prevPos(pos) });
      else return;
      e.preventDefault();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pos]);

  const slide = SLIDES[pos.i];
  const next = SLIDES[pos.i + 1];
  const total = SLIDES.reduce((a, b) => a + b.seconds, 0);
  const target = SLIDES.slice(0, pos.i + 1).reduce((a, b) => a + b.seconds, 0);
  const elapsed = t0 && now ? (now - t0) / 1000 : 0;
  const ahead = target - elapsed;

  return (
    <div style={{ position: "fixed", inset: 0, background: "#120c08", color: "#f6efe4", padding: 32, overflow: "auto", fontSize: 22 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div className="font-display" style={{ fontSize: 44 }}>
          {pos.i + 1}/{SLIDES.length} · {slide.title}
          <span style={{ fontSize: 26, color: "#cbb9a3", marginLeft: 16 }}>
            {QUARTER[slide.quarter].short} · click {pos.s + 1} of {slide.steps}
          </span>
        </div>
        <div className="font-display tabular" style={{ fontSize: 56, color: ahead >= 0 ? "#1aa87e" : "#e86a2e" }}>
          {mmss(elapsed)} <span style={{ fontSize: 26, color: "#cbb9a3" }}>/ {mmss(total)} · slide ends at {mmss(target)}</span>
        </div>
      </div>
      <ul style={{ fontSize: 30, lineHeight: 1.5, marginTop: 24 }}>
        {slide.notes.map((n, k) => <li key={k}>{n}</li>)}
      </ul>
      <div style={{ marginTop: 24, color: "#cbb9a3" }}>
        Next: {next ? `${next.title} (${next.seconds}s)` : "end"} · This slide: {slide.seconds}s
      </div>
      <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
        <button onClick={() => ch.current?.postMessage({ type: "go", pos: prevPos(pos) })} style={btn}>◀ Back</button>
        <button onClick={() => ch.current?.postMessage({ type: "go", pos: nextPos(pos) })} style={btn}>Next ▶</button>
        <button onClick={() => ch.current?.postMessage({ type: "reset" })} style={btn}>Reset clock</button>
      </div>
    </div>
  );
}

const btn: CSSProperties = {
  fontSize: 22, padding: "10px 20px", borderRadius: 10, border: "1px solid #f5b83d", background: "#1c1510", color: "#f6efe4", cursor: "pointer",
};
