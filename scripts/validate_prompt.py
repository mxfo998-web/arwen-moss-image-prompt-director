#!/usr/bin/env python3
"""Validate MOSS drafts/final prompts and recover editable drafts.

Uses the unmodified upstream compiler as the schema authority.
Python standard library only. Does not submit image generation.
"""

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path

from compile_prompt import compile_prompt, reject_constant, unique_object


def read_json(path):
    return json.loads(
        Path(path).read_text(encoding="utf-8-sig"),
        object_pairs_hook=unique_object,
        parse_constant=reject_constant,
    )


def dimensions(width, height):
    for name, value in (("width", width), ("height", height)):
        if type(value) is not int or value <= 0 or value % 16:
            raise ValueError(f"{name} must be a positive integer multiple of 16")


def recover_draft(prompt, width, height):
    dimensions(width, height)
    required = {"summary", "items", "bbox_coord_space", "bbox_format"}
    if not isinstance(prompt, dict) or set(prompt) != required:
        raise ValueError("Compiled Layout must contain exactly summary/items/coordinate markers")
    if prompt["bbox_coord_space"] != "abs_centralized" or prompt["bbox_format"] != "yxyx":
        raise ValueError("Compiled coordinates must be abs_centralized / yxyx")
    if not isinstance(prompt["items"], list) or not prompt["items"]:
        raise ValueError("Compiled items must be a nonempty flat array")
    result = copy.deepcopy(prompt)
    result.update(width=width, height=height, bbox_coord_space="abs", bbox_format="xyxy")
    for index, item in enumerate(result["items"]):
        if not isinstance(item, dict):
            raise ValueError(f"items[{index}] must be an object")
        box = item.get("bbox")
        if not isinstance(box, list) or len(box) != 4 or any(type(v) is not int for v in box):
            raise ValueError(f"items[{index}].bbox must contain four integers")
        y1, x1, y2, x2 = box
        item["bbox"] = [x1 + width // 2, y1 + height // 2,
                        x2 + width // 2, y2 + height // 2]
    # Reuse all upstream field/boundary/text checks, and verify lossless recovery.
    recompilation = json.loads(compile_prompt(result))
    if recompilation != prompt:
        raise ValueError("Compiled Layout does not round-trip through the official schema")
    return result


def visible_strings(layout):
    if "caption" in layout:
        return None
    return [item["text"] for item in layout["items"] if item["label"] == "text"]


def check_expected(actual, expected, caption=None):
    if not isinstance(expected, list) or any(not isinstance(s, str) or not s for s in expected):
        raise ValueError("Expected text file must be an array of nonempty strings")
    if caption is not None:
        for value, count in Counter(expected).items():
            if caption.count(value) < count:
                raise ValueError(f"Caption does not preserve expected literal text: {value!r}")
        return "caption-substring-only"
    if Counter(actual) != Counter(expected):
        raise ValueError("Layout text items do not exactly match expected strings and multiplicities")
    return "layout-exact"


def validate_file(path, kind, width=None, height=None, expected=None):
    path = Path(path)
    if kind == "caption":
        value = path.read_text(encoding="utf-8-sig")
        if not value.strip():
            raise ValueError("Caption must be nonempty")
        report = {"valid": True, "kind": "caption"}
        if expected is not None:
            report["text_check"] = check_expected(None, expected, caption=value)
        return report, None
    value = read_json(path)
    if kind == "compiled":
        if width is None or height is None:
            raise ValueError("Compiled validation requires --width and --height")
        draft = recover_draft(value, width, height)
    else:
        compile_prompt(value)
        draft = value
    strings = visible_strings(draft)
    report = {"valid": True, "kind": kind,
              "items": len(draft.get("items", [])),
              "text_items": 0 if strings is None else len(strings)}
    if "width" in draft:
        report.update(width=draft["width"], height=draft["height"])
    if expected is not None:
        report["text_check"] = check_expected(
            strings, expected, caption=draft["caption"] if strings is None else None)
    return report, draft


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--kind", choices=("draft", "compiled", "caption"), required=True)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--expect-text", type=Path, help="JSON array; exact Layout text multiset")
    parser.add_argument("--draft-output", type=Path, help="Recover compiled Layout using the given canvas")
    args = parser.parse_args()
    try:
        expected = read_json(args.expect_text) if args.expect_text else None
        report, draft = validate_file(args.input, args.kind, args.width, args.height, expected)
        if args.draft_output:
            if args.kind != "compiled":
                raise ValueError("--draft-output is available only for compiled Layout")
            if args.draft_output.resolve() == args.input.resolve():
                raise ValueError("Recovered draft must not overwrite the model prompt")
            args.draft_output.parent.mkdir(parents=True, exist_ok=True)
            args.draft_output.write_text(
                json.dumps(draft, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                encoding="utf-8",
            )
            report["draft_output"] = str(args.draft_output)
        print(json.dumps(report, ensure_ascii=True))
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, ensure_ascii=True), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
