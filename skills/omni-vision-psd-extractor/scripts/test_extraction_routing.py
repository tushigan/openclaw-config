#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from extract_layers import build_extraction_prompt
from layer_plan_common import build_initial_state, build_parallel_plan


def fixture_manifest() -> dict:
    return {
        "canvas": {"width": 623, "height": 820},
        "layout_ref": "/tmp/source.png",
        "background_raw_path": "/tmp/job/raw/background.png",
        "layers": [
            {
                "key": "background",
                "group": "01_BG",
                "name": "Background",
                "prompt": "background",
                "left": 0,
                "top": 0,
                "width": 623,
                "height": 820,
                "raw_path": "/tmp/job/raw/background.png",
                "layer_path": "/tmp/job/layers/background.png",
            },
            {
                "key": "foreground",
                "group": "05_FOREGROUND",
                "name": "Foreground",
                "prompt": "foreground",
                "left": 0,
                "top": 0,
                "width": 623,
                "height": 820,
                "raw_path": "/tmp/job/raw/foreground.png",
                "layer_path": "/tmp/job/layers/foreground.png",
            },
        ],
    }


def assert_close_ratio(size: str, expected_ratio: float) -> None:
    width, height = map(int, size.split("x"))
    actual_ratio = width / height
    assert abs(actual_ratio - expected_ratio) < 0.02, (size, actual_ratio, expected_ratio)


def test_two_layer_routing() -> None:
    plan = build_parallel_plan(fixture_manifest())
    tasks = plan["tasks"]
    assert [task["key"] for task in tasks] == ["background", "foreground"]
    assert [task["kind"] for task in tasks] == ["background", "foreground"]
    assert list(build_initial_state(plan)["tasks"]) == ["background", "foreground"]

    expected_ratio = 623 / 820
    for task in tasks:
        assert_close_ratio(task["size_plan"]["suggested_size"], expected_ratio)

    background_prompt = build_extraction_prompt(tasks[0])
    foreground_prompt = build_extraction_prompt(tasks[1])

    assert background_prompt.startswith("将图片中的背景提取出来")
    assert "Holographic Extraction" in background_prompt
    assert "Total Visual Element Disassembly" not in background_prompt
    assert "Total Visual Element Disassembly" in foreground_prompt


if __name__ == "__main__":
    test_two_layer_routing()
    print("extraction routing ok")
