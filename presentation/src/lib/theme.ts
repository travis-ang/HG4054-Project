import raw from "@/data/results.json";

/** All numbers on the slides come from results.json (written by scripts/export_site_data.py). */
export const R = raw;

/** Basketball theme: dark hardwood under arena lights, chalk-white lines, trophy gold, scoreboard LEDs. */
export const C = {
  bg: "#120c08",       // arena floor at the edges
  floor: "#2a1c12",    // lit hardwood (charts drawn straight on the floor sit on this)
  surface: "#1c1510",  // cards and panels
  surface2: "#2a2018",
  cream: "#f6efe4",    // chalk white
  muted: "#cbb9a3",
  dim: "#8f7c66",
  gold: "#f5b83d",     // trophy gold: kickers, highlights, active card
  ball: "#f26a1b",     // basketball orange: ball, rim, painted keys (decoration only)
  led: "#ffb547",      // scoreboard LED amber
  ledRed: "#ff4d3a",   // shot-clock red
  ink: "#1a1108",      // dark text on gold
  i: "#b48cf2",
  we: "#4fc9e0",
  grid: "rgba(246,239,228,0.13)",
  line: "rgba(246,239,228,0.09)",
};

/** hex colour + alpha (0-1) -> #rrggbbaa */
export const a = (hex: string, alpha: number) => hex + Math.round(alpha * 255).toString(16).padStart(2, "0");

export type Tier = "role" | "starter" | "superstar";
export const TIERS: Tier[] = ["role", "starter", "superstar"];
// Validated on the card (#1c1510) and the lit floor (#2c1e13) (dataviz validator, dark mode, all pairs): all checks pass.
// "I"/"we" (#b48cf2/#4fc9e0): CVD and normal-vision checks pass; lighter than the mark band because they colour words, always labelled.
export const TIER_COLOR: Record<Tier, string> = { role: "#e86a2e", starter: "#1aa87e", superstar: "#4a90ec" };
export const TIER_NAME: Record<Tier, string> = { role: "Role player", starter: "Starter", superstar: "Superstar" };

export const P = {
  lebron: { id: 2544, name: "LeBron James", tier: "superstar" as Tier },
  curry: { id: 201939, name: "Stephen Curry", tier: "superstar" as Tier },
  durant: { id: 201142, name: "Kevin Durant", tier: "superstar" as Tier },
  kobe: { id: 977, name: "Kobe Bryant", tier: "superstar" as Tier },
  wade: { id: 2548, name: "Dwyane Wade", tier: "superstar" as Tier },
  duncan: { id: 1495, name: "Tim Duncan", tier: "superstar" as Tier },
  dirk: { id: 1717, name: "Dirk Nowitzki", tier: "superstar" as Tier },
  tatum: { id: 1628369, name: "Jayson Tatum", tier: "superstar" as Tier },
  holiday: { id: 201950, name: "Jrue Holiday", tier: "starter" as Tier },
  horford: { id: 201143, name: "Al Horford", tier: "starter" as Tier },
  dgreen: { id: 201980, name: "Danny Green", tier: "starter" as Tier },
  billups: { id: 1497, name: "Chauncey Billups", tier: "starter" as Tier },
  ginobili: { id: 1938, name: "Manu Ginóbili", tier: "role" as Tier },
  iguodala: { id: 2738, name: "Andre Iguodala", tier: "role" as Tier },
  livingston: { id: 2733, name: "Shaun Livingston", tier: "role" as Tier },
  haslem: { id: 2617, name: "Udonis Haslem", tier: "role" as Tier },
  caruso: { id: 1627936, name: "Alex Caruso", tier: "role" as Tier },
  draymond: { id: 203110, name: "Draymond Green", tier: "superstar" as Tier },
  klay: { id: 202691, name: "Klay Thompson", tier: "superstar" as Tier },
};

/** Percentage points with a real minus sign: -0.0041 -> "−0.4". */
export const pp = (x: number, d = 1) => `${x >= 0 ? "+" : "−"}${Math.abs(x * 100).toFixed(d)}`;
export const pct = (x: number, d = 1) => (x * 100).toFixed(d);
export const lin = (d0: number, d1: number, r0: number, r1: number) => (v: number) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
export const ease = [0.22, 1, 0.36, 1] as const;
