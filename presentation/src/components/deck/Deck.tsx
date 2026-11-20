"use client";

import { AnimatePresence, motion, MotionConfig } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";
import Chrome from "./Chrome";
import Court from "./Court";
import Stage from "./Stage";
import { nextPos, prevPos, SLIDES } from "@/slides";
import { Pos } from "@/slides/types";

export const CHANNEL = "hg4054-deck";

const variants = {
  enter: (d: number) => ({ opacity: 0, x: d * 90, filter: "blur(10px)" }),
  center: { opacity: 1, x: 0, filter: "blur(0px)", transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] as const } },
  exit: (d: number) => ({ opacity: 0, x: d * -90, filter: "blur(10px)", transition: { duration: 0.32 } }),
};

/**
 * Keys: → / Space / PageDown next build · ← / PageUp back · ↓ ↑ whole slides · Home / End
 *       F full screen · T rehearsal clock · N notes · C face-cam layout · P presenter window · R reset clock
 */
export default function Deck() {
  const [shown, setShown] = useState<Pos>({ i: 0, s: 0 });
  const [dir, setDir] = useState(1);
  const [banner, setBanner] = useState<number | null>(null);
  const [hud, setHud] = useState(false);
  const [notes, setNotes] = useState(false);
  const [cam, setCam] = useState(false);
  const [t0, setT0] = useState<number | null>(null);
  const [now, setNow] = useState(0);
  const cur = useRef<Pos>({ i: 0, s: 0 });
  const timers = useRef<number[]>([]);
  const chan = useRef<BroadcastChannel | null>(null);
  const t0Ref = useRef<number | null>(null);

  const go = useCallback((np: Pos, broadcast = true) => {
    const old = cur.current;
    if (np.i === old.i && np.s === old.s) return;
    timers.current.forEach((t) => window.clearTimeout(t));
    timers.current = [];
    setDir(np.i > old.i || (np.i === old.i && np.s >= old.s) ? 1 : -1);
    cur.current = np;
    const qNew = SLIDES[np.i].quarter;
    if (np.i > old.i && qNew !== SLIDES[old.i].quarter && qNew >= 1 && qNew <= 4) {
      setBanner(qNew);
      timers.current.push(window.setTimeout(() => setShown(np), 850));
      timers.current.push(window.setTimeout(() => setBanner(null), 1500));
    } else {
      setBanner(null);
      setShown(np);
    }
    window.history.replaceState(null, "", `#/${np.i + 1}/${np.s}`);
    if (t0Ref.current === null) {
      t0Ref.current = Date.now();
      setT0(t0Ref.current);
    }
    if (broadcast) chan.current?.postMessage({ type: "pos", pos: np, t0: t0Ref.current });
  }, []);

  // start position from the URL hash (#/slide/step), so a reload stays put
  useEffect(() => {
    const m = window.location.hash.match(/^#\/(\d+)(?:\/(\d+))?/);
    if (!m) return;
    const i = Math.min(Math.max(+m[1] - 1, 0), SLIDES.length - 1);
    const s = Math.min(+(m[2] ?? 0), SLIDES[i].steps - 1);
    cur.current = { i, s };
    setShown({ i, s });
  }, []);

  // presenter window sync
  useEffect(() => {
    const ch = new BroadcastChannel(CHANNEL);
    chan.current = ch;
    ch.onmessage = (e) => {
      if (e.data?.type === "go") go(e.data.pos);
      if (e.data?.type === "hello") ch.postMessage({ type: "pos", pos: cur.current, t0: t0Ref.current });
      if (e.data?.type === "reset") {
        t0Ref.current = Date.now();
        setT0(t0Ref.current);
        ch.postMessage({ type: "pos", pos: cur.current, t0: t0Ref.current });
      }
    };
    return () => ch.close();
  }, [go]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const k = e.key;
      if (["ArrowRight", " ", "PageDown", "Enter"].includes(k)) go(nextPos(cur.current));
      else if (["ArrowLeft", "PageUp", "Backspace"].includes(k)) go(prevPos(cur.current));
      else if (k === "ArrowDown") go({ i: Math.min(cur.current.i + 1, SLIDES.length - 1), s: 0 });
      else if (k === "ArrowUp") go({ i: Math.max(cur.current.i - 1, 0), s: 0 });
      else if (k === "Home") go({ i: 0, s: 0 });
      else if (k === "End") go({ i: SLIDES.length - 1, s: 0 });
      else if (k === "f" || k === "F") {
        if (document.fullscreenElement) document.exitFullscreen();
        else document.documentElement.requestFullscreen();
      } else if (k === "t" || k === "T") setHud((h) => !h);
      else if (k === "n" || k === "N") setNotes((n) => !n);
      else if (k === "c" || k === "C") setCam((c) => !c);
      else if (k === "p" || k === "P") window.open("/presenter", "hg4054-presenter", "width=1100,height=800");
      else if (k === "r" || k === "R") {
        t0Ref.current = Date.now();
        setT0(t0Ref.current);
      } else return;
      e.preventDefault();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go]);

  useEffect(() => {
    if (!hud && !notes) return;
    const id = window.setInterval(() => setNow(Date.now()), 500);
    return () => window.clearInterval(id);
  }, [hud, notes]);

  const slide = SLIDES[shown.i];
  const Comp = slide.Comp;
  const elapsed = t0 && now ? Math.max(0, (now - t0) / 1000) : 0;

  return (
    <MotionConfig reducedMotion="never">
      <Stage cam={cam}>
        <div style={{ position: "absolute", inset: 0 }} onClick={() => go(nextPos(cur.current))}>
          <Court quarter={slide.quarter} />
          <AnimatePresence mode="wait" custom={dir}>
            <motion.div
              key={shown.i}
              custom={dir}
              variants={variants}
              initial="enter"
              animate="center"
              exit="exit"
              style={{ position: "absolute", inset: 0 }}
            >
              <Comp step={shown.s} />
            </motion.div>
          </AnimatePresence>
          <Chrome slides={SLIDES} i={shown.i} s={shown.s} banner={banner} hud={hud} notes={notes} elapsed={elapsed} />
        </div>
      </Stage>
    </MotionConfig>
  );
}
