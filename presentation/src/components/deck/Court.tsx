"use client";

import { motion } from "framer-motion";

// Full court, 94 x 50 ft drawn at about 19 px per foot (baskets 5.25 ft from the baselines).
const LINES = [
  "M60 61 H1860 V1018 H60 Z",                                   // boundary
  "M960 61 V1018",                                              // half-court line
  "M1075 540 A115 115 0 1 1 845 540 A115 115 0 1 1 1075 540",   // centre circle
  "M60 387 H424 V693 H60",                                      // left key
  "M1860 387 H1496 V693 H1860",                                 // right key
  "M424 425 A115 115 0 0 1 424 655 A115 115 0 0 1 424 425",     // left free-throw circle
  "M1496 425 A115 115 0 0 0 1496 655 A115 115 0 0 0 1496 425",  // right free-throw circle
  "M60 118 H330 A455 455 0 0 1 330 961 H60",                    // left three-point line
  "M1860 118 H1590 A455 455 0 0 0 1590 961 H1860",              // right three-point line
  "M160 463 A77 77 0 0 1 160 617",                              // left restricted arc
  "M1760 463 A77 77 0 0 0 1760 617",                            // right restricted arc
  "M136 483 V597",                                              // left backboard
  "M1784 483 V597",                                             // right backboard
];

// Maple boards running the length of the court; fixed seed so server and browser draw the same floor.
const TONES = ["#4b321d", "#523720", "#462f1b", "#4f3520", "#583b22", "#432c19", "#4d331e"];
const PLANKS = (() => {
  let seed = 11;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const out: { x: number; y: number; w: number; c: string }[] = [];
  for (let y = 0; y < 1080; y += 27) {
    let x = -rnd() * 420;
    while (x < 1920) {
      const w = 380 + rnd() * 560;
      out.push({ x, y, w, c: TONES[Math.floor(rnd() * TONES.length)] });
      x += w;
    }
  }
  return out;
})();

export default function Court({ quarter }: { quarter: number }) {
  return (
    <div style={{ position: "absolute", inset: 0, background: "#1d130b" }}>
      {/* hardwood */}
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0 }}>
        <defs>
          <filter id="woodgrain" x="0" y="0" width="100%" height="100%">
            <feTurbulence type="fractalNoise" baseFrequency="0.0032 0.12" numOctaves="3" seed="4" />
            <feColorMatrix type="matrix" values="0 0 0 0 0.10  0 0 0 0 0.06  0 0 0 0 0.03  0 0 0 1.3 -0.45" />
          </filter>
        </defs>
        {PLANKS.map((p, k) => (
          <rect key={k} x={p.x} y={p.y} width={p.w - 2} height={25.5} fill={p.c} />
        ))}
        <rect width="1920" height="1080" filter="url(#woodgrain)" opacity="0.55" />
        {/* painted keys and centre circle */}
        <path d="M60 387 H424 V693 H60 Z" fill="#f26a1b" fillOpacity="0.16" />
        <path d="M1860 387 H1496 V693 H1860 Z" fill="#f26a1b" fillOpacity="0.16" />
        <circle cx="960" cy="540" r="115" fill="#f26a1b" fillOpacity="0.12" />
      </svg>
      {/* court lines, redrawn at the start of each quarter */}
      <svg key={quarter} width="1920" height="1080" style={{ position: "absolute", inset: 0 }}>
        {LINES.map((d, i) => (
          <motion.path
            key={i}
            d={d}
            fill="none"
            stroke="#f6efe4"
            strokeOpacity={0.2}
            strokeWidth={5}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 2.2, delay: 0.05 * i, ease: [0.65, 0, 0.35, 1] }}
          />
        ))}
        <circle cx="160" cy="540" r="13" fill="none" stroke="#f26a1b" strokeOpacity="0.4" strokeWidth="4" />
        <circle cx="1760" cy="540" r="13" fill="none" stroke="#f26a1b" strokeOpacity="0.4" strokeWidth="4" />
      </svg>
      {/* arena lighting: dim the floor, a warm pool of light in the middle, reflections of the light rig */}
      <div
        style={{
          position: "absolute", inset: 0,
          background:
            "radial-gradient(300px 70px at 22% 9%, rgba(255,226,180,0.10), transparent 70%)," +
            "radial-gradient(300px 70px at 50% 6%, rgba(255,226,180,0.12), transparent 70%)," +
            "radial-gradient(300px 70px at 78% 9%, rgba(255,226,180,0.10), transparent 70%)," +
            "radial-gradient(1250px 800px at 50% 40%, rgba(8,5,3,0.42), rgba(8,5,3,0.66) 62%, rgba(5,3,2,0.9) 100%)",
        }}
      />
      {/* film grain */}
      <svg width="1920" height="1080" style={{ position: "absolute", inset: 0, opacity: 0.06, mixBlendMode: "overlay" }}>
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" stitchTiles="stitch" />
        </filter>
        <rect width="1920" height="1080" filter="url(#grain)" />
      </svg>
    </div>
  );
}
