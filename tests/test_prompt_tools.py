"""Contract tests for geometry, literal text, import/export and CLI safety."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compile_prompt import compile_prompt, reject_constant, unique_object
from validate_prompt import check_expected, recover_draft, validate_file, visible_strings


def draft():
    return {
        "width": 1536, "height": 1024, "bbox_coord_space": "abs", "bbox_format": "xyxy",
        "summary": {"canvas": "single", "caption": "象牙白陶瓷杯与中文文案"},
        "items": [
            {"label": "object", "caption": "一只象牙白陶瓷杯", "bbox": [176, 224, 800, 864]},
            {"label": "text", "caption": "深绿色标题", "text": "一杯温暖\n一刻从容",
             "bbox": [928, 272, 1408, 448]},
        ],
    }


class GeometryContract(unittest.TestCase):
    def test_known_upstream_example_and_unicode(self):
        result = compile_prompt(draft())
        self.assertEqual(json.loads(result)["items"][0]["bbox"], [-288, -592, 352, 32])
        self.assertEqual(json.loads(result)["items"][1]["text"], "一杯温暖\n一刻从容")
        self.assertEqual(len(result.splitlines()), 1)
        self.assertNotIn("width", json.loads(result))

    def test_fractional_edges_enclose_before_centering(self):
        value = draft()
        value.update(width=16, height=16)
        value["items"] = [{"label": "object", "caption": "陶瓷杯", "bbox": [1.25, 2.25, 14.1, 15.1]}]
        self.assertEqual(json.loads(compile_prompt(value))["items"][0]["bbox"], [-6, -7, 8, 7])

    def test_full_canvas_and_overlapping_boxes_are_valid(self):
        value = draft()
        value["items"][0]["bbox"] = [0, 0, 1536, 1024]
        result = json.loads(compile_prompt(value))
        self.assertEqual(result["items"][0]["bbox"], [-512, -768, 512, 768])

    def test_non_multiple_canvas_rejected(self):
        value = draft()
        value["width"] = 1537
        with self.assertRaises(ValueError):
            compile_prompt(value)

    def test_outside_and_reversed_boxes_rejected(self):
        for bad in ([-1, 0, 50, 50], [10, 10, 5, 50], [0, 0, 1537, 50]):
            value = draft()
            value["items"][0]["bbox"] = bad
            with self.subTest(box=bad), self.assertRaises(ValueError):
                compile_prompt(value)

    def test_missing_text_and_unknown_fields_rejected(self):
        for mutate in ("missing_text", "unknown_root", "unknown_item"):
            value = draft()
            if mutate == "missing_text":
                del value["items"][1]["text"]
            elif mutate == "unknown_root":
                value["camera"] = "low angle"
            else:
                value["items"][0]["font_size"] = 20
            with self.subTest(case=mutate), self.assertRaises(ValueError):
                compile_prompt(value)

    def test_boolean_and_nonfinite_coordinates_rejected(self):
        for number in (True, float("nan"), float("inf")):
            value = draft()
            value["items"][0]["bbox"][0] = number
            with self.subTest(number=number), self.assertRaises(ValueError):
                compile_prompt(value)

    def test_duplicate_keys_and_invalid_json_numbers_rejected(self):
        for raw in ('{"caption":"a","caption":"b"}', '{"caption":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)


class RecoveryAndText(unittest.TestCase):
    def test_compiled_recovery_is_lossless(self):
        source = draft()
        compiled = json.loads(compile_prompt(source))
        self.assertEqual(recover_draft(compiled, 1536, 1024), source)

    def test_recovery_rejects_bad_markers_extra_fields_and_nonintegers(self):
        source = json.loads(compile_prompt(draft()))
        cases = []
        a = copy.deepcopy(source); a["bbox_format"] = "xyxy"; cases.append(a)
        a = copy.deepcopy(source); a["width"] = 1536; cases.append(a)
        a = copy.deepcopy(source); a["items"][0]["bbox"][0] = -288.0; cases.append(a)
        a = copy.deepcopy(source); a["items"][0]["bbox"][0] = True; cases.append(a)
        a = copy.deepcopy(source); a["items"][0]["bbox"][0] = -513; cases.append(a)
        for item in cases:
            with self.subTest(item=item), self.assertRaises(ValueError):
                recover_draft(item, 1536, 1024)

    def test_expected_text_is_exact_not_normalized(self):
        self.assertEqual(check_expected(["你好！", "你好！"], ["你好！", "你好！"]), "layout-exact")
        for expected in (["你好!"], ["你好！"], ["你好！", "你好！", "额外"]):
            with self.subTest(expected=expected), self.assertRaises(ValueError):
                check_expected(["你好！", "你好！"], expected)

    def test_caption_preserves_visible_newlines(self):
        text = "纸上写着“一杯温暖\n一刻从容”。"
        self.assertEqual(check_expected(None, ["一杯温暖\n一刻从容"], caption=text),
                         "caption-substring-only")

    def test_layout_without_text_and_plain_caption(self):
        value = draft()
        value["items"] = value["items"][:1]
        self.assertEqual(visible_strings(value), [])
        self.assertEqual(compile_prompt({"caption": "安静的电影静帧。"}), "安静的电影静帧。")


class CommandLineContract(unittest.TestCase):
    def run_tool(self, script, *args):
        return subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts" / script), *map(str, args)],
                              capture_output=True, encoding="utf-8")

    def test_compile_validate_and_recover_files(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            src, final, restored = directory / "source.json", directory / "prompt.txt", directory / "restored.json"
            src.write_text(json.dumps(draft(), ensure_ascii=False), encoding="utf-8")
            result = self.run_tool("compile_prompt.py", src, "--output", final)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = self.run_tool("validate_prompt.py", final, "--kind", "compiled",
                                   "--width", 1536, "--height", 1024, "--draft-output", restored)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["valid"])
            self.assertEqual(json.loads(restored.read_text(encoding="utf-8")), draft())

    def test_canvas_is_required_for_compiled_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prompt.txt"
            path.write_text(compile_prompt(draft()), encoding="utf-8")
            result = self.run_tool("validate_prompt.py", path, "--kind", "compiled")
            self.assertEqual(result.returncode, 2)

    def test_input_files_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.json"
            original = json.dumps(draft(), ensure_ascii=False)
            path.write_text(original, encoding="utf-8")
            result = self.run_tool("compile_prompt.py", path, "--output", path)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_bom_and_exact_copy_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "draft.json"
            path.write_text(json.dumps(draft(), ensure_ascii=False), encoding="utf-8-sig")
            report, _ = validate_file(path, "draft", expected=["一杯温暖\n一刻从容"])
            self.assertEqual(report["text_check"], "layout-exact")


if __name__ == "__main__":
    unittest.main()
