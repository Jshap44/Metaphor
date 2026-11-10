"""Protect the student-facing interface against raw code-like output panels."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_pages_do_not_render_raw_json_or_code():
    for name in ('energy_dashboard.py', 'app.py'):
        tree = ast.parse((ROOT / name).read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'st':
                assert node.func.attr not in ('json', 'code', 'echo', 'text'), (name, node.lineno)


def test_presentation_helpers_are_syntactically_valid():
    ast.parse((ROOT / 'ui_presenters.py').read_text(encoding='utf-8'))
