import assert from "node:assert/strict";
import test from "node:test";
import { getExifOrientationStyle } from "./image-orientation.ts";

test("maps all EXIF orientation values to CSS transforms", () => {
  const expected = [
    "none",
    "scaleX(-1)",
    "rotate(180deg)",
    "scaleY(-1)",
    "rotate(90deg) scaleY(-1)",
    "rotate(90deg)",
    "rotate(90deg) scaleX(-1)",
    "rotate(270deg)",
  ];

  expected.forEach((transform, index) => {
    assert.equal(getExifOrientationStyle(index + 1).transform, transform);
  });
});

test("uses portrait-fit dimensions for quarter-turn orientations", () => {
  for (const orientation of [5, 6, 7, 8]) {
    assert.equal(getExifOrientationStyle(orientation).width, "75%");
    assert.equal(getExifOrientationStyle(orientation).height, "75%");
  }
  assert.equal(getExifOrientationStyle(3).width, undefined);
});

test("unknown orientation values leave the image unchanged", () => {
  assert.equal(getExifOrientationStyle("unknown").transform, "none");
});