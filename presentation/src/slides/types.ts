import type { ReactElement } from "react";

export type SlideProps = { step: number };

export type SlideDef = {
  id: string;
  quarter: number; // 0 tip-off, 1-4 the four required parts, 5 final
  title: string;
  steps: number; // clicks on this slide (1 = no builds)
  seconds: number; // planned speaking time
  notes: string[]; // speaking prompts, not a script
  Comp: (p: SlideProps) => ReactElement;
};

export type Pos = { i: number; s: number };

export const QUARTER: Record<number, { short: string; label: string; long: string }> = {
  0: { short: "TIP", label: "Tip-off", long: "Tip-off" },
  1: { short: "Q1", label: "Motivation", long: "1st quarter" },
  2: { short: "Q2", label: "Data & methods", long: "2nd quarter" },
  3: { short: "Q3", label: "Results", long: "3rd quarter" },
  4: { short: "Q4", label: "Discussion", long: "4th quarter" },
  5: { short: "FIN", label: "Final", long: "Final buzzer" },
};
