import { useEffect, useState } from "react";

function clamp(value) {
  return Math.max(0, Math.min(1, value));
}

function easeOutCubic(value) {
  return 1 - Math.pow(1 - value, 3);
}

export function useMotionProgress(key, durationMs = 1200) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (typeof window === "undefined") {
      setProgress(1);
      return undefined;
    }

    const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    if (reducedMotion) {
      setProgress(1);
      return undefined;
    }

    let frame = 0;
    let startedAt = 0;
    setProgress(0);

    const tick = (timestamp) => {
      if (!startedAt) {
        startedAt = timestamp;
      }
      const raw = clamp((timestamp - startedAt) / durationMs);
      setProgress(easeOutCubic(raw));
      if (raw < 1) {
        frame = window.requestAnimationFrame(tick);
      }
    };

    frame = window.requestAnimationFrame(tick);
    return () => {
      if (frame) {
        window.cancelAnimationFrame(frame);
      }
    };
  }, [key, durationMs]);

  return progress;
}
