from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from quote_skill.layout import build_stage_table_sections


def _fail(message: str) -> None:
    raise SystemExit(message)


def validate_merge_semantics(content_path: Path, html_path: Path) -> None:
    content = json.loads(content_path.read_text(encoding="utf-8"))
    html_text = html_path.read_text(encoding="utf-8")

    forbidden_markers = [
        '<td class="block"></td>',
        '<td class="project"></td>',
    ]
    for marker in forbidden_markers:
        if marker in html_text:
            _fail(
                "检测到空白单元格伪合并结构。请不要手写空白 <td> 模拟合并，"
                "而是回到 quote-content.json 用正式渲染器生成 rowspan。"
            )

    sections = build_stage_table_sections(content)
    for section in sections:
        stage_name = html.escape(section["stage_name"])
        rows = section["rows"]
        if len(rows) > 1:
            expected = f'rowspan="{len(rows)}">{stage_name}</td>'
            if expected not in html_text:
                _fail(f"阶段“{section['stage_name']}”应合并 {len(rows)} 行，但 HTML 中没找到对应 rowspan。")

        for row in rows:
            if row["show_project"] and row["project_rowspan"] > 1:
                project_name = html.escape(row["project_name"])
                expected = f'rowspan="{row["project_rowspan"]}">{project_name}</td>'
                if expected not in html_text:
                    _fail(
                        f"项目“{row['project_name']}”应合并 {row['project_rowspan']} 行，但 HTML 中没找到对应 rowspan。"
                    )

                deliverables_text = row["deliverables_text"]
                if deliverables_text:
                    escaped_deliverables = html.escape(deliverables_text)
                    deliverable_expected = (
                        f'rowspan="{row["project_rowspan"]}">{escaped_deliverables}</td>'
                    )
                    if deliverable_expected not in html_text:
                        _fail(
                            f"项目“{row['project_name']}”的交付物应合并 {row['project_rowspan']} 行，"
                            "但 HTML 中没找到对应 rowspan。"
                        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", required=True, help="quote-content.json path")
    parser.add_argument("--html", required=True, help="quote.html path")
    args = parser.parse_args()

    validate_merge_semantics(Path(args.content), Path(args.html))
    print("Merge semantics OK")


if __name__ == "__main__":
    main()
