import { useEffect, useRef, useState } from "react";

interface ScoreReadoutProps {
  value: number;
  size?: "sm" | "lg";
}

export function ScoreReadout({ value, size = "sm" }: ScoreReadoutProps) {
  const [flip, setFlip] = useState(false);
  const prev = useRef(value);

  useEffect(() => {
    if (Math.abs(prev.current - value) > 0.001) {
      setFlip(true);
      const t = setTimeout(() => setFlip(false), 260);
      prev.current = value;
      return () => clearTimeout(t);
    }
  }, [value]);

  const display = (value * 10).toFixed(2);

  return (
    <span className={`score-readout score-readout--${size} ${flip ? "score-readout--flip" : ""}`}>
      {display}
    </span>
  );
}
