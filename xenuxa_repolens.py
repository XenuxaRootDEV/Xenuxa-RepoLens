#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║             XENUXA REPOLENS — Production-Grade Edition           ║
║          Elite Repository Intelligence & Analytics Engine        ║
║                  Copyright © 2025  Xenuxa Corp.                  ║
╚══════════════════════════════════════════════════════════════════╝

A self-contained, single-file Python utility that recursively scans
a directory, builds a live Rich TUI tree, counts Lines of Code per
language, and exports a professional Markdown report.

Requirements:
    pip install rich

Usage:
    python xenuxa_repolens.py [path]          # scan <path>
    python xenuxa_repolens.py                 # scan current directory
"""

from __future__ import annotations

import os
import sys
import time
import signal
import datetime
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator, Union, Any

# ── third-party ──────────────────────────────────────────────────────────────
try:
    from rich import print as rprint
    from rich.align import Align
    from rich.columns import Columns
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.rule import Rule
    from rich.style import Style
    from rich.table import Table
    from rich.text import Text
    from rich.tree import Tree
except ImportError:
    print(
        "\n[ERROR] The 'rich' library is not installed.\n"
        "  Install it with:  pip install rich\n"
    )
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL CONSOLE
# ─────────────────────────────────────────────────────────────────────────────

console: Console = Console(highlight=False)

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

EXPORT_FILENAME: str = "xenuxa_structure.md"

# Directories to skip during traversal — order matters for fast set lookup
IGNORED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "__pycache__",
        "node_modules",
        ".vs",
        ".vscode",
        "bin",
        "obj",
        "venv",
        ".venv",
        "env",
        ".env",
        ".idea",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        "dist",
        "build",
        ".cache",
        ".gradle",
        ".angular",
        "coverage",
        ".nyc_output",
        "vendor",
        "Pods",
        ".DS_Store",
        "target",         # Rust / Maven
        ".cargo",
        ".stack-work",    # Haskell
        "htmlcov",
        ".eggs",
    }
)

# Files to skip (exact name matches)
IGNORED_FILES: frozenset[str] = frozenset(
    {
        EXPORT_FILENAME,
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
    }
)

# ── Extension → (language label, Rich colour, display emoji) ─────────────────
EXT_META: Dict[str, Tuple[str, str, str]] = {
    # Python
    ".py":       ("Python",         "bold green",          "🐍"),
    ".pyw":      ("Python",         "bold green",          "🐍"),
    ".pyi":      ("Python Stub",    "green",               "🐍"),
    # Web
    ".js":       ("JavaScript",     "bold yellow",         "📜"),
    ".mjs":      ("JavaScript",     "bold yellow",         "📜"),
    ".cjs":      ("JavaScript",     "bold yellow",         "📜"),
    ".jsx":      ("JavaScript JSX", "yellow",              "⚛️ "),
    ".ts":       ("TypeScript",     "bold cyan",           "🔷"),
    ".tsx":      ("TypeScript TSX", "cyan",                "🔷"),
    ".html":     ("HTML",           "bold orange1",        "🌐"),
    ".htm":      ("HTML",           "bold orange1",        "🌐"),
    ".css":      ("CSS",            "bold blue",           "🎨"),
    ".scss":     ("SCSS",           "blue",                "🎨"),
    ".sass":     ("Sass",           "blue",                "🎨"),
    ".less":     ("Less",           "blue",                "🎨"),
    # C family
    ".c":        ("C",              "bold bright_red",     "⚙️ "),
    ".h":        ("C Header",       "red",                 "⚙️ "),
    ".cpp":      ("C++",            "bold red",            "⚙️ "),
    ".cxx":      ("C++",            "bold red",            "⚙️ "),
    ".cc":       ("C++",            "bold red",            "⚙️ "),
    ".hpp":      ("C++ Header",     "red",                 "⚙️ "),
    # C# / .NET
    ".cs":       ("C#",             "bold magenta",        "🟣"),
    ".vb":       ("VB.NET",         "magenta",             "🟣"),
    ".fs":       ("F#",             "magenta",             "🟣"),
    ".fsx":      ("F# Script",      "magenta",             "🟣"),
    # JVM
    ".java":     ("Java",           "bold bright_yellow",  "☕"),
    ".kt":       ("Kotlin",         "bold bright_yellow",  "☕"),
    ".kts":      ("Kotlin Script",  "bright_yellow",       "☕"),
    ".scala":    ("Scala",          "bright_red",          "☕"),
    ".groovy":   ("Groovy",         "bright_red",          "☕"),
    ".gradle":   ("Gradle",         "bright_red",          "🔧"),
    # Go
    ".go":       ("Go",             "bold bright_cyan",    "🐹"),
    # Rust
    ".rs":       ("Rust",           "bold bright_red",     "🦀"),
    # Ruby
    ".rb":       ("Ruby",           "bold red",            "💎"),
    ".rake":     ("Ruby Rake",      "red",                 "💎"),
    ".gemspec":  ("Ruby GemSpec",   "red",                 "💎"),
    # PHP
    ".php":      ("PHP",            "bold bright_blue",    "🐘"),
    # Shell
    ".sh":       ("Shell",          "bold green",          "🖥️ "),
    ".bash":     ("Bash",           "bold green",          "🖥️ "),
    ".zsh":      ("Zsh",            "bold green",          "🖥️ "),
    ".fish":     ("Fish",           "bold green",          "🖥️ "),
    ".ps1":      ("PowerShell",     "bright_blue",         "🖥️ "),
    ".psm1":     ("PowerShell",     "bright_blue",         "🖥️ "),
    # Data / Config
    ".json":     ("JSON",           "bright_yellow",       "📋"),
    ".jsonc":    ("JSON",           "bright_yellow",       "📋"),
    ".yaml":     ("YAML",           "bright_yellow",       "📋"),
    ".yml":      ("YAML",           "bright_yellow",       "📋"),
    ".toml":     ("TOML",           "bright_yellow",       "📋"),
    ".ini":      ("INI",            "yellow",              "📋"),
    ".cfg":      ("Config",         "yellow",              "📋"),
    ".conf":     ("Config",         "yellow",              "📋"),
    ".env":      ("Env File",       "yellow",              "🔑"),
    ".xml":      ("XML",            "bright_yellow",       "📋"),
    # Docs
    ".md":       ("Markdown",       "bold bright_blue",    "📝"),
    ".mdx":      ("MDX",            "bold bright_blue",    "📝"),
    ".rst":      ("reStructuredText","bright_blue",        "📝"),
    ".txt":      ("Text",           "white",               "📄"),
    ".tex":      ("LaTeX",          "white",               "📝"),
    # SQL
    ".sql":      ("SQL",            "bold bright_cyan",    "🗄️ "),
    # Swift / ObjC
    ".swift":    ("Swift",          "bold bright_red",     "🍎"),
    ".m":        ("Objective-C",    "bright_red",          "🍎"),
    ".mm":       ("Objective-C++",  "bright_red",          "🍎"),
    # Dart / Flutter
    ".dart":     ("Dart",           "bold bright_cyan",    "🎯"),
    # Lua
    ".lua":      ("Lua",            "bold blue",           "🌙"),
    # Perl
    ".pl":       ("Perl",           "bright_magenta",      "🐪"),
    ".pm":       ("Perl Module",    "bright_magenta",      "🐪"),
    # R
    ".r":        ("R",              "bright_blue",         "📊"),
    ".R":        ("R",              "bright_blue",         "📊"),
    # Julia
    ".jl":       ("Julia",          "bright_magenta",      "🔬"),
    # Haskell
    ".hs":       ("Haskell",        "bright_magenta",      "λ "),
    ".lhs":      ("Haskell Lit.",   "bright_magenta",      "λ "),
    # Elixir / Erlang
    ".ex":       ("Elixir",         "bright_magenta",      "💧"),
    ".exs":      ("Elixir Script",  "bright_magenta",      "💧"),
    ".erl":      ("Erlang",         "bright_red",          "💧"),
    ".hrl":      ("Erlang Header",  "bright_red",          "💧"),
    # Clojure
    ".clj":      ("Clojure",        "bright_green",        "🟢"),
    ".cljs":     ("ClojureScript",  "bright_green",        "🟢"),
    ".cljc":     ("Clojure",        "bright_green",        "🟢"),
    # Docker / CI
    ".dockerfile": ("Dockerfile",   "bright_blue",         "🐳"),
    ".dockerignore": ("Docker",     "blue",                "🐳"),
    # Misc build / tooling
    ".makefile": ("Makefile",       "bright_green",        "🔧"),
    ".mk":       ("Makefile",       "bright_green",        "🔧"),
    ".cmake":    ("CMake",          "bright_green",        "🔧"),
    ".nix":      ("Nix",            "bright_blue",         "❄️ "),
    ".tf":       ("Terraform",      "bright_magenta",      "🏗️ "),
    ".tfvars":   ("Terraform",      "bright_magenta",      "🏗️ "),
    ".graphql":  ("GraphQL",        "bright_magenta",      "⬡ "),
    ".gql":      ("GraphQL",        "bright_magenta",      "⬡ "),
    ".proto":    ("Protobuf",       "bright_cyan",         "📦"),
    ".wasm":     ("WebAssembly",    "bright_blue",         "🕸️ "),
    ".wat":      ("WebAssembly Txt","bright_blue",         "🕸️ "),
    ".vue":      ("Vue",            "bright_green",        "💚"),
    ".svelte":   ("Svelte",         "bright_red",          "🔥"),
    ".astro":    ("Astro",          "bright_magenta",      "🚀"),
    ".njk":      ("Nunjucks",       "bright_yellow",       "🌀"),
    ".jinja":    ("Jinja",          "bright_yellow",       "🌀"),
    ".j2":       ("Jinja2",         "bright_yellow",       "🌀"),
    ".ipynb":    ("Jupyter",        "bright_yellow",       "📓"),
}

# Special exact-name matches (e.g. "Dockerfile", "Makefile" without extension)
NAME_META: Dict[str, Tuple[str, str, str]] = {
    "Dockerfile":       ("Dockerfile",  "bright_blue",  "🐳"),
    "dockerfile":       ("Dockerfile",  "bright_blue",  "🐳"),
    "Makefile":         ("Makefile",    "bright_green", "🔧"),
    "makefile":         ("Makefile",    "bright_green", "🔧"),
    "GNUmakefile":      ("Makefile",    "bright_green", "🔧"),
    ".gitignore":       ("Git",         "white",        "🔧"),
    ".gitattributes":   ("Git",         "white",        "🔧"),
    ".editorconfig":    ("EditorCfg",   "white",        "🔧"),
    "Procfile":         ("Procfile",    "bright_yellow","🔧"),
    "Vagrantfile":      ("Vagrant",     "bright_blue",  "🔧"),
    "Gemfile":          ("Ruby",        "bold red",     "💎"),
    "Rakefile":         ("Ruby",        "red",          "💎"),
    "Podfile":          ("CocoaPods",   "bright_red",   "🍎"),
    "Brewfile":         ("Homebrew",    "bright_yellow","🍺"),
    "Justfile":         ("Just",        "bright_green", "🔧"),
    "justfile":         ("Just",        "bright_green", "🔧"),
    "CMakeLists.txt":   ("CMake",       "bright_green", "🔧"),
    ".eslintrc":        ("ESLint",      "bright_yellow","🔧"),
    ".prettierrc":      ("Prettier",    "bright_yellow","🔧"),
    ".babelrc":         ("Babel",       "bright_yellow","🔧"),
    "pyproject.toml":   ("Python Cfg",  "bold green",   "🐍"),
    "setup.py":         ("Python Cfg",  "bold green",   "🐍"),
    "setup.cfg":        ("Python Cfg",  "bold green",   "🐍"),
    "requirements.txt": ("Python Deps", "green",        "🐍"),
    "Pipfile":          ("Pipfile",     "green",        "🐍"),
    "poetry.lock":      ("Poetry Lock", "green",        "🐍"),
    "package.json":     ("NPM Pkg",     "bright_yellow","📦"),
    "package-lock.json":("NPM Lock",    "yellow",       "📦"),
    "yarn.lock":        ("Yarn Lock",   "bright_blue",  "📦"),
    "pnpm-lock.yaml":   ("PNPM Lock",   "bright_blue",  "📦"),
    "composer.json":    ("Composer",    "bright_blue",  "🐘"),
    "composer.lock":    ("Comp. Lock",  "blue",         "🐘"),
    "go.mod":           ("Go Module",   "bright_cyan",  "🐹"),
    "go.sum":           ("Go Sum",      "bright_cyan",  "🐹"),
    "Cargo.toml":       ("Cargo",       "bright_red",   "🦀"),
    "Cargo.lock":       ("Cargo Lock",  "red",          "🦀"),
    "build.gradle":     ("Gradle",      "bright_red",   "☕"),
    "pom.xml":          ("Maven POM",   "bright_yellow","☕"),
    "build.sbt":        ("SBT",         "bright_red",   "☕"),
    "pubspec.yaml":     ("Dart Pub",    "bright_cyan",  "🎯"),
}

# ─────────────────────────────────────────────────────────────────────────────
#  DATA TYPES
# ─────────────────────────────────────────────────────────────────────────────

class LanguageStat:
    """Accumulates per-language file count and line-of-code totals."""

    __slots__ = ("language", "emoji", "files", "lines")

    def __init__(self, language: str, emoji: str) -> None:
        self.language: str = language
        self.emoji: str = emoji
        self.files: int = 0
        self.lines: int = 0

    def add(self, lines: int) -> None:
        self.files += 1
        self.lines += lines


class ScanResult:
    """Aggregated output produced by the scan engine."""

    __slots__ = ("root_path", "tree", "stats", "total_files", "total_lines",
                 "skipped_files", "duration_seconds", "plain_tree_lines")

    def __init__(self, root_path: Path) -> None:
        self.root_path: Path = root_path
        self.tree: Optional[Tree] = None
        self.stats: Dict[str, LanguageStat] = {}
        self.total_files: int = 0
        self.total_lines: int = 0
        self.skipped_files: int = 0
        self.duration_seconds: float = 0.0
        self.plain_tree_lines: List[str] = []


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_file_meta(filename: str) -> Tuple[str, str, str]:
    """
    Return (language_label, rich_colour, emoji) for a given filename.
    Priority: exact name match → extension match → fallback.
    """
    # 1. Exact name match
    if filename in NAME_META:
        return NAME_META[filename]

    # 2. Extension match
    ext: str = Path(filename).suffix.lower()
    if ext and ext in EXT_META:
        return EXT_META[ext]

    # 3. Fallback
    return ("Other", "white", "📄")


def _count_lines(filepath: Path) -> int:
    """
    Safely count lines in a file.

    Encoding cascade:
        utf-8  →  latin-1  →  utf-8 with 'replace' errors

    Returns 0 on PermissionError or any irrecoverable IO error.
    """
    encodings: List[str] = ["utf-8", "latin-1"]
    for enc in encodings:
        try:
            with filepath.open("r", encoding=enc) as fh:
                return sum(1 for _ in fh)
        except UnicodeDecodeError:
            continue
        except PermissionError:
            return 0
        except OSError:
            return 0

    # Final fallback: utf-8 with replacement characters
    try:
        with filepath.open("r", encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except (OSError, PermissionError):
        return 0


def _human_size(num_bytes: int) -> str:
    """Convert bytes to a human-readable string (e.g. 3.2 MB)."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:,.1f} {unit}"
        num_bytes = int(num_bytes / 1024.0)
    return f"{num_bytes:,.1f} PB"


def _truncate(s: str, max_len: int = 60) -> str:
    """Truncate a string with an ellipsis if it exceeds max_len."""
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


# ─────────────────────────────────────────────────────────────────────────────
#  CORE SCAN ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _walk_directory(
    path: Path,
    rich_node: Tree,
    plain_lines: List[str],
    stats: Dict[str, LanguageStat],
    result: ScanResult,
    progress: Progress,
    task_id: Any,
    prefix: str = "",
    depth: int = 0,
) -> None:
    """
    Recursive, depth-first directory walker using os.scandir.

    Mutates *rich_node* (Rich Tree) and *plain_lines* (list of strings
    for the Markdown export) in place.

    Args:
        path:        Directory to scan.
        rich_node:   Parent Rich Tree node.
        plain_lines: Accumulator for plain-text tree output.
        stats:       Per-language stat accumulator.
        result:      Top-level ScanResult object.
        progress:    Rich Progress instance.
        task_id:     Progress task identifier.
        prefix:      ASCII prefix for plain-text tree rendering.
        depth:       Current recursion depth (used for indentation).
    """
    try:
        entries: List[os.DirEntry[str]] = sorted(
            os.scandir(path),
            key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower()),
        )
    except PermissionError:
        rich_node.add(Text("⛔ [Permission Denied]", style="dim red"))
        plain_lines.append(f"{prefix}    ⛔ [Permission Denied]")
        return
    except OSError as exc:
        rich_node.add(Text(f"⚠️  [{exc.strerror}]", style="dim red"))
        plain_lines.append(f"{prefix}    ⚠️  [{exc.strerror}]")
        return

    total: int = len(entries)

    for idx, entry in enumerate(entries):
        is_last: bool = idx == total - 1
        connector: str = "└── " if is_last else "├── "
        child_prefix: str = prefix + ("    " if is_last else "│   ")

        # ── DIRECTORY ─────────────────────────────────────────────────────
        if entry.is_dir(follow_symlinks=False):
            if entry.name in IGNORED_DIRS:
                skipped_label = Text(
                    f"📁 {entry.name}  [skipped]", style="dim italic"
                )
                rich_node.add(skipped_label)
                plain_lines.append(f"{prefix}{connector}📁 {entry.name}  [skipped]")
                continue

            dir_label = Text()
            dir_label.append("📁 ", style="bold")
            dir_label.append(entry.name, style="bold bright_white")
            dir_label.append("/", style="dim white")

            child_rich_node: Tree = rich_node.add(dir_label)
            plain_lines.append(f"{prefix}{connector}📁 {entry.name}/")

            _walk_directory(
                path=Path(entry.path),
                rich_node=child_rich_node,
                plain_lines=plain_lines,
                stats=stats,
                result=result,
                progress=progress,
                task_id=task_id,
                prefix=child_prefix,
                depth=depth + 1,
            )

        # ── FILE ──────────────────────────────────────────────────────────
        else:
            if entry.name in IGNORED_FILES:
                continue

            file_path: Path = Path(entry.path)
            language, colour, emoji = _get_file_meta(entry.name)

            # Count lines
            loc: int = _count_lines(file_path)

            # Update stats
            if language not in stats:
                stats[language] = LanguageStat(language=language, emoji=emoji)
            stats[language].add(loc)

            result.total_files += 1
            result.total_lines += loc

            # File size
            try:
                size_bytes: int = entry.stat().st_size
                size_str: str = _human_size(size_bytes)
            except OSError:
                size_str = "?"

            # Build Rich file label
            file_label = Text()
            file_label.append(f"{emoji} ", style="")
            file_label.append(_truncate(entry.name, 50), style=colour)
            file_label.append(f"  ({loc:,} loc, {size_str})", style="dim")

            rich_node.add(file_label)
            plain_lines.append(
                f"{prefix}{connector}{emoji} {entry.name}  ({loc:,} loc)"
            )

            # Update progress
            progress.advance(task_id)
            progress.update(
                task_id,
                description=(
                    f"[cyan]Scanning[/cyan] [dim]{_truncate(entry.name, 35)}[/dim]"
                ),
            )


def run_scan(root_path: Path) -> ScanResult:
    """
    Orchestrate the full directory scan, returning a populated ScanResult.

    Displays a live Rich progress bar during the traversal.
    """
    result: ScanResult = ScanResult(root_path=root_path)
    stats: Dict[str, LanguageStat] = {}
    plain_lines: List[str] = []

    root_label = Text()
    root_label.append("📁 ", style="bold")
    root_label.append(str(root_path.resolve()), style="bold bright_white")
    root_label.append("/", style="dim")

    rich_tree: Tree = Tree(
        root_label,
        guide_style="bold bright_black",
    )

    plain_lines.append(f"📁 {root_path.resolve()}/")

    progress: Progress = Progress(
        SpinnerColumn(spinner_name="dots12", style="bold cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30, style="cyan", complete_style="bold cyan"),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )

    t0: float = time.perf_counter()

    with progress:
        task_id = progress.add_task("[cyan]Initialising scan…[/cyan]", total=None)

        _walk_directory(
            path=root_path,
            rich_node=rich_tree,
            plain_lines=plain_lines,
            stats=stats,
            result=result,
            progress=progress,
            task_id=task_id,
            prefix="",
            depth=0,
        )

    result.duration_seconds = time.perf_counter() - t0
    result.tree = rich_tree
    result.stats = stats
    result.plain_tree_lines = plain_lines

    return result


# ─────────────────────────────────────────────────────────────────────────────
#  MARKDOWN EXPORTER
# ─────────────────────────────────────────────────────────────────────────────

def _build_markdown_report(result: ScanResult) -> str:
    """
    Build the complete Markdown report string from a ScanResult.
    """
    now: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    root_str: str = str(result.root_path.resolve())

    sorted_stats: List[LanguageStat] = sorted(
        result.stats.values(), key=lambda s: s.lines, reverse=True
    )
    total_lines: int = result.total_lines if result.total_lines > 0 else 1  # avoid /0

    lines: List[str] = []

    # ── Header ───────────────────────────────────────────────────────────────
    lines.append("# 🔍 Xenuxa RepoLens — Repository Analysis Report")
    lines.append("")
    lines.append("> Generated by **Xenuxa RepoLens** — Elite Repository Intelligence Engine")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Metadata table ────────────────────────────────────────────────────────
    lines.append("## 📋 Scan Metadata")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("|---|---|")
    lines.append(f"| **Root Path** | `{root_str}` |")
    lines.append(f"| **Scan Date** | {now} |")
    lines.append(f"| **Duration** | {result.duration_seconds:.3f}s |")
    lines.append(f"| **Total Files** | {result.total_files:,} |")
    lines.append(f"| **Total Lines of Code** | {result.total_lines:,} |")
    lines.append(f"| **Languages Detected** | {len(result.stats)} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Language metrics table ────────────────────────────────────────────────
    lines.append("## 📊 Language Metrics")
    lines.append("")
    lines.append("| # | Language | Files | Lines of Code (LoC) | Share |")
    lines.append("|---|---|---:|---:|---:|")

    for rank, stat in enumerate(sorted_stats, start=1):
        pct: float = (stat.lines / total_lines) * 100.0
        bar_filled: int = int(pct / 5)  # 20-char wide bar
        bar_empty: int = 20 - bar_filled
        bar: str = "█" * bar_filled + "░" * bar_empty
        lines.append(
            f"| {rank} | {stat.emoji} **{stat.language}** | "
            f"{stat.files:,} | "
            f"{stat.lines:,} | "
            f"`{bar}` {pct:.1f}% |"
        )

    lines.append("")
    lines.append(
        f"| | **TOTAL** | **{result.total_files:,}** | "
        f"**{result.total_lines:,}** | **100%** |"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Directory tree ────────────────────────────────────────────────────────
    lines.append("## 🗂️  Directory Structure")
    lines.append("")
    lines.append("```text")
    for tree_line in result.plain_tree_lines:
        lines.append(tree_line)
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Footer ────────────────────────────────────────────────────────────────
    lines.append(
        "_Report generated by [Xenuxa RepoLens](https://xenuxa.dev) — "
        "Elite Repository Intelligence Engine._"
    )
    lines.append("")

    return "\n".join(lines)


def export_markdown(result: ScanResult) -> Path:
    """
    Write the Markdown report to <root_path>/xenuxa_structure.md.
    Returns the output path on success.
    """
    output_path: Path = result.root_path.resolve() / EXPORT_FILENAME
    report_content: str = _build_markdown_report(result)

    try:
        output_path.write_text(report_content, encoding="utf-8")
    except PermissionError as exc:
        console.print(
            f"[bold red]⚠️  Could not write report to {output_path}: {exc}[/bold red]"
        )
        # Fallback: write to current working directory
        fallback_path: Path = Path.cwd() / EXPORT_FILENAME
        fallback_path.write_text(report_content, encoding="utf-8")
        return fallback_path

    return output_path


# ─────────────────────────────────────────────────────────────────────────────
#  RICH TUI — BANNER
# ─────────────────────────────────────────────────────────────────────────────

ASCII_ART: str = r"""
██╗  ██╗███████╗███╗   ██╗██╗   ██╗██╗  ██╗ █████╗
╚██╗██╔╝██╔════╝████╗  ██║██║   ██║╚██╗██╔╝██╔══██╗
 ╚███╔╝ █████╗  ██╔██╗ ██║██║   ██║ ╚███╔╝ ███████║
 ██╔██╗ ██╔══╝  ██║╚██╗██║██║   ██║ ██╔██╗ ██╔══██║
██╔╝ ██╗███████╗██║ ╚████║╚██████╔╝██╔╝ ██╗██║  ██║
╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝

██████╗ ███████╗██████╗  ██████╗ ██╗     ███████╗███╗   ██╗███████╗
██╔══██╗██╔════╝██╔══██╗██╔═══██╗██║     ██╔════╝████╗  ██║██╔════╝
██████╔╝█████╗  ██████╔╝██║   ██║██║     █████╗  ██╔██╗ ██║███████╗
██╔══██╗██╔══╝  ██╔═══╝ ██║   ██║██║     ██╔══╝  ██║╚██╗██║╚════██║
██║  ██║███████╗██║     ╚██████╔╝███████╗███████╗██║ ╚████║███████║
╚═╝  ╚═╝╚══════╝╚═╝      ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝
"""


def _print_banner() -> None:
    """Render the branded startup banner to the console."""

    art_text = Text(ASCII_ART, style="bold cyan", justify="center")

    tagline = Text(
        "  Elite Repository Intelligence & Analytics Engine  ",
        style="bold bright_white on #0a2a3a",
        justify="center",
    )

    version_line = Text(
        "v2.0  •  Production Grade  •  © 2025 Xenuxa Corp.",
        style="dim cyan",
        justify="center",
    )

    banner_panel = Panel(
        Align.center(
            Text.assemble(
                art_text,
                "\n",
                tagline,
                "\n\n",
                version_line,
            )
        ),
        border_style="bold cyan",
        padding=(1, 4),
    )

    console.print()
    console.print(banner_panel)
    console.print()


# ─────────────────────────────────────────────────────────────────────────────
#  RICH TUI — RESULTS DISPLAY
# ─────────────────────────────────────────────────────────────────────────────

def _build_stats_table(result: ScanResult) -> Table:
    """Construct the per-language statistics Rich Table."""

    table = Table(
        title="📊  Language Analytics",
        title_style="bold bright_white",
        header_style="bold cyan",
        border_style="cyan",
        show_lines=True,
        expand=False,
        min_width=72,
    )

    table.add_column("#",             style="dim",              justify="right",  width=4)
    table.add_column("Language",      style="bold",             justify="left",   min_width=20)
    table.add_column("Files",         style="bright_yellow",    justify="right",  width=8)
    table.add_column("Lines of Code", style="bright_green",     justify="right",  width=16)
    table.add_column("Share",         style="bright_cyan",      justify="left",   min_width=24)

    sorted_stats: List[LanguageStat] = sorted(
        result.stats.values(), key=lambda s: s.lines, reverse=True
    )
    total_lines: int = result.total_lines if result.total_lines > 0 else 1

    for rank, stat in enumerate(sorted_stats, start=1):
        pct: float = (stat.lines / total_lines) * 100.0
        bar_width: int = 18
        filled: int = int((pct / 100) * bar_width)
        empty: int = bar_width - filled

        # Colour the bar based on share
        if pct >= 40:
            bar_colour = "bold bright_green"
        elif pct >= 15:
            bar_colour = "bold bright_cyan"
        elif pct >= 5:
            bar_colour = "bold bright_yellow"
        else:
            bar_colour = "dim"

        bar_text = Text()
        bar_text.append("█" * filled, style=bar_colour)
        bar_text.append("░" * empty, style="dim")
        bar_text.append(f"  {pct:.1f}%", style="bold white")

        lang_text = Text()
        lang_text.append(f"{stat.emoji} ", style="")
        lang_text.append(stat.language, style="bold")

        table.add_row(
            str(rank),
            lang_text,
            f"{stat.files:,}",
            f"{stat.lines:,}",
            bar_text,
        )

    # Totals footer row
    table.add_section()
    total_label = Text()
    total_label.append("Σ  TOTAL", style="bold bright_white")

    table.add_row(
        "",
        total_label,
        Text(f"{result.total_files:,}", style="bold bright_yellow"),
        Text(f"{result.total_lines:,}", style="bold bright_green"),
        Text("100%", style="bold bright_cyan"),
    )

    return table


def _print_summary(result: ScanResult, export_path: Path) -> None:
    """Render the final results panel including tree, stats table, and footer."""

    # ── Summary metrics strip ─────────────────────────────────────────────────
    summary_table = Table.grid(expand=True, padding=(0, 4))
    summary_table.add_column(justify="center")
    summary_table.add_column(justify="center")
    summary_table.add_column(justify="center")
    summary_table.add_column(justify="center")

    def _metric(label: str, value: str, colour: str = "bright_cyan") -> Text:
        t = Text(justify="center")
        t.append(f"{value}\n", style=f"bold {colour}")
        t.append(label, style="dim")
        return t

    summary_table.add_row(
        _metric("Root Path", _truncate(str(result.root_path.resolve()), 30), "bright_white"),
        _metric("Total Files", f"{result.total_files:,}", "bright_yellow"),
        _metric("Total LoC", f"{result.total_lines:,}", "bright_green"),
        _metric("Scan Time", f"{result.duration_seconds:.3f}s", "bright_cyan"),
    )

    summary_panel = Panel(
        summary_table,
        title="[bold cyan]⚡  Scan Summary[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print(summary_panel)
    console.print()

    # ── Directory tree ────────────────────────────────────────────────────────
    console.print(
        Panel(
            result.tree,
            title="[bold cyan]🗂️   Directory Structure[/bold cyan]",
            border_style="bright_black",
            padding=(1, 2),
        )
    )
    console.print()

    # ── Stats table ───────────────────────────────────────────────────────────
    stats_table: Table = _build_stats_table(result)
    console.print(Align.center(stats_table))
    console.print()

    # ── Export confirmation ───────────────────────────────────────────────────
    export_panel = Panel(
        Text.assemble(
            ("✅  Report exported → ", "bold bright_green"),
            (str(export_path), "bold bright_white underline"),
        ),
        border_style="bright_green",
        padding=(0, 2),
    )
    console.print(export_panel)
    console.print()

    # ── Final rule ────────────────────────────────────────────────────────────
    console.print(
        Rule(
            title="[dim]Xenuxa RepoLens — Scan Complete[/dim]",
            style="dim cyan",
        )
    )
    console.print()


# ─────────────────────────────────────────────────────────────────────────────
#  SIGNAL HANDLING
# ─────────────────────────────────────────────────────────────────────────────

def _install_signal_handlers() -> None:
    """
    Install a SIGINT handler that prints a clean cancellation message
    via Rich instead of dumping a raw Python traceback.
    """

    def _handle_sigint(signum: int, frame: Any) -> None:  # noqa: ANN001
        console.print()
        console.print(
            Panel(
                Text(
                    "🛑  Scan cancelled by user  (SIGINT received)",
                    style="bold bright_yellow",
                    justify="center",
                ),
                border_style="yellow",
                padding=(0, 4),
            )
        )
        console.print()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_sigint)


# ─────────────────────────────────────────────────────────────────────────────
#  ARGUMENT PARSING  (stdlib only — no argparse dependency beyond stdlib)
# ─────────────────────────────────────────────────────────────────────────────

def _parse_args() -> Path:
    """
    Parse CLI arguments and return the target directory path.

    Usage:
        python xenuxa_repolens.py [path]
    """
    if len(sys.argv) >= 2:
        raw: str = sys.argv[1]

        # Handle --help / -h
        if raw in ("-h", "--help"):
            console.print()
            console.print(
                Panel(
                    Text.assemble(
                        ("Usage\n\n",             "bold bright_white"),
                        ("  python xenuxa_repolens.py [path]\n\n", "bright_cyan"),
                        ("Arguments\n\n",         "bold bright_white"),
                        ("  path  ", "bold cyan"),
                        ("Directory to scan. Defaults to the current working directory.\n\n",
                         "white"),
                        ("Options\n\n",           "bold bright_white"),
                        ("  -h, --help  ", "bold cyan"),
                        ("Show this help message and exit.\n",   "white"),
                    ),
                    title="[bold cyan]Xenuxa RepoLens — Help[/bold cyan]",
                    border_style="cyan",
                    padding=(1, 4),
                )
            )
            console.print()
            sys.exit(0)

        target: Path = Path(raw).resolve()
    else:
        target = Path.cwd()

    if not target.exists():
        console.print(
            f"[bold red]✗  Path does not exist:[/bold red] [bright_white]{target}[/bright_white]"
        )
        sys.exit(1)

    if not target.is_dir():
        console.print(
            f"[bold red]✗  Path is not a directory:[/bold red] [bright_white]{target}[/bright_white]"
        )
        sys.exit(1)

    return target


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Primary execution entry point.

    Flow:
        1. Install signal handlers.
        2. Parse CLI arguments.
        3. Print branded banner.
        4. Run the directory scan with live progress.
        5. Display results (tree + stats table).
        6. Export the Markdown report.
    """
    _install_signal_handlers()

    target_path: Path = _parse_args()

    _print_banner()

    # Pre-scan info panel
    console.print(
        Panel(
            Text.assemble(
                ("🎯  Target  ", "bold bright_white"),
                (str(target_path), "bold bright_cyan underline"),
            ),
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()
    console.print(Rule(style="dim cyan"))
    console.print()

    # ── Run scan ──────────────────────────────────────────────────────────────
    result: ScanResult = run_scan(target_path)

    # ── Export Markdown report ────────────────────────────────────────────────
    export_path: Path = export_markdown(result)

    # ── Display results ───────────────────────────────────────────────────────
    _print_summary(result, export_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Secondary safety net — should normally be caught by SIGINT handler
        console.print()
        console.print(
            Panel(
                Text(
                    "🛑  Scan cancelled by user.",
                    style="bold bright_yellow",
                    justify="center",
                ),
                border_style="yellow",
                padding=(0, 4),
            )
        )
        console.print()
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        console.print_exception(show_locals=False)
        console.print()
        console.print(
            Panel(
                Text.assemble(
                    ("💥  Unexpected error: ", "bold red"),
                    (str(exc),                 "bright_white"),
                ),
                border_style="red",
                padding=(0, 2),
            )
        )
        sys.exit(1)