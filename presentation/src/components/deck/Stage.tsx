"use client";

import { ReactNode, useEffect, useState } from "react";

export const W = 1920;
export const H = 1080;

/** A fixed 1920x1080 canvas scaled to the window. `cam` leaves the right quarter free for a face cam. */
export default function Stage({ children, cam = false }: { children: ReactNode; cam?: boolean }) {
  const [vp, setVp] = useState({ w: W, h: H });
  useEffect(() => {
    const f = () => setVp({ w: window.innerWidth, h: window.innerHeight });
    f();
    window.addEventListener("resize", f);
    return () => window.removeEventListener("resize", f);
  }, []);
  const s = Math.min((vp.w * (cam ? 0.75 : 1)) / W, vp.h / H);
  const left = cam ? 0 : (vp.w - W * s) / 2;
  const top = (vp.h - H * s) / 2;
  return (
    <div style={{ position: "fixed", inset: 0, background: "#080504", overflow: "hidden" }}>
      <div
        style={{
          position: "absolute", left, top, width: W, height: H, transform: `scale(${s})`,
          transformOrigin: "0 0", overflow: "hidden",
        }}
      >
        {children}
      </div>
    </div>
  );
}
