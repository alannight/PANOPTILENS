import type { CSSProperties } from "react";

const orientationTransforms: Record<number, string> = {
  1: "none",
  2: "scaleX(-1)",
  3: "rotate(180deg)",
  4: "scaleY(-1)",
  5: "rotate(90deg) scaleY(-1)",
  6: "rotate(90deg)",
  7: "rotate(90deg) scaleX(-1)",
  8: "rotate(270deg)",
};

export function getExifOrientationStyle(value: string | number | null): CSSProperties {
  const orientation = Number(value);
  const transform = orientationTransforms[orientation] ?? "none";
  const quarterTurn = orientation >= 5 && orientation <= 8;

  return {
    transform,
    transformOrigin: "center",
    imageOrientation: "none",
    ...(quarterTurn ? { width: "75%", height: "75%" } : {}),
  };
}