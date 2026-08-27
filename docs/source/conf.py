"""Sphinx configuration for the SimpleBGC32 Python API documentation."""

from __future__ import annotations

from dataclasses import is_dataclass
from pathlib import Path
import sys

DOCS_SOURCE = Path(__file__).resolve().parent
PROJECT_ROOT = DOCS_SOURCE.parents[1]
sys.path.insert(0, str(DOCS_SOURCE))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from theme_colors import CLASSIC_THEME_OPTIONS

project = "SimpleBGC32 Python API"
copyright = "BaseCam Electronics"
author = "Nikita Toporkov"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

autodoc_typehints = "description"
autodoc_member_order = "bysource"
autodoc_class_signature = "mixed"
toc_object_entries_show_parents = "hide"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ["_templates"]
exclude_patterns = ["_build"]
html_theme = "classic"
html_theme_options = CLASSIC_THEME_OPTIONS
html_static_path = ["_static"]
html_css_files = ["basecam.css"]


def hide_dataclass_constructor_signature(
    app: object,
    what: str,
    name: str,
    obj: object,
    options: object,
    signature: str | None,
    return_annotation: str | None,
) -> tuple[str, str | None] | None:
    """Keep generated dataclass constructors out of the public API reference."""
    if what == "class" and is_dataclass(obj):
        return "", return_annotation
    return None


def setup(app: object) -> None:
    app.connect("autodoc-process-signature", hide_dataclass_constructor_signature)
