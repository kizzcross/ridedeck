import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { MotionConfig } from "framer-motion";

type Pref = "system" | "reduce" | "full";

interface MotionCtx {
  /** Effective decision: should we suppress non-essential motion? */
  reduceMotion: boolean;
  /** The user's explicit preference (system follows the OS setting). */
  pref: Pref;
  setPref: (p: Pref) => void;
}

const Ctx = createContext<MotionCtx>({ reduceMotion: false, pref: "system", setPref: () => {} });
const STORAGE_KEY = "rd-motion-pref";

function systemPrefersReduced(): boolean {
  return typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

/** Central motion policy. Combines the OS `prefers-reduced-motion` setting with
 *  an explicit in-app toggle, and configures framer-motion accordingly so every
 *  animated component degrades to a static state when motion is reduced. */
export function MotionProvider({ children }: { children: React.ReactNode }) {
  const [pref, setPrefState] = useState<Pref>(() => {
    return (typeof localStorage !== "undefined" && (localStorage.getItem(STORAGE_KEY) as Pref)) || "system";
  });
  const [systemReduced, setSystemReduced] = useState(systemPrefersReduced);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setSystemReduced(mq.matches);
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);

  const setPref = useCallback((p: Pref) => {
    setPrefState(p);
    localStorage.setItem(STORAGE_KEY, p);
  }, []);

  const reduceMotion = pref === "reduce" || (pref === "system" && systemReduced);

  const value = useMemo(() => ({ reduceMotion, pref, setPref }), [reduceMotion, pref, setPref]);

  return (
    <Ctx.Provider value={value}>
      <MotionConfig reducedMotion={reduceMotion ? "always" : "never"}>{children}</MotionConfig>
    </Ctx.Provider>
  );
}

export function useMotionPref() {
  return useContext(Ctx);
}

/** Convenience: `true` when non-essential animation should be skipped. */
export function useReduceMotion() {
  return useContext(Ctx).reduceMotion;
}
