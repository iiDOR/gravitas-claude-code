#!/usr/bin/env python3
"""Gravitas Living Knowledge Engine (GKE) for Claude Code.

Maintains a persistent, self-updating Knowledge Base in .gravitas/knowledge/.
Eliminates blind reconnaissance, tracks architectural invariants, and
incrementally updates as code changes. Zero dependencies (Python standard library only).
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

KNOWLEDGE_DIR = Path(".gravitas") / "knowledge"
MODULES_DIR = KNOWLEDGE_DIR / "modules"
INDEX_FILE = KNOWLEDGE_DIR / "index.json"

IGNORE_DIRS = {
    ".git", ".gravitas", ".agents", ".gemini", "node_modules", "target",
    "build", "dist", "venv", ".venv", "__pycache__", ".idea", ".vscode"
}

def sha256_file(path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def load_index() -> dict:
    """Load index.json or return empty schema."""
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "version": 1,
        "repo_name": Path.cwd().name,
        "cards": {},
        "tracked_files": {},
        "metadata": {
            "created_at": None,
            "last_updated": None
        }
    }

def save_index(index: dict):
    """Save index.json atomically."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not index.get("metadata", {}).get("created_at"):
        index.setdefault("metadata", {})["created_at"] = now
    index.setdefault("metadata", {})["last_updated"] = now
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def detect_project_context(root: Path) -> dict:
    """Detect language, build system, and test commands from project files."""
    info = {
        "languages": [],
        "build_system": None,
        "test_cmd": None,
        "lint_cmd": None,
        "entry_points": []
    }

    # Node / TS
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})
            info["languages"].append("TypeScript" if (root / "tsconfig.json").exists() else "JavaScript")
            info["build_system"] = "npm"
            if "test" in scripts:
                info["test_cmd"] = "npm test"
            if "lint" in scripts:
                info["lint_cmd"] = "npm run lint"
            if "main" in data:
                info["entry_points"].append(data["main"])
        except Exception:
            pass

    # Rust
    cargo_toml = root / "Cargo.toml"
    if cargo_toml.exists():
        info["languages"].append("Rust")
        info["build_system"] = "cargo"
        info["test_cmd"] = "cargo test"
        info["lint_cmd"] = "cargo clippy"
        if (root / "src" / "main.rs").exists():
            info["entry_points"].append("src/main.rs")
        if (root / "src" / "lib.rs").exists():
            info["entry_points"].append("src/lib.rs")

    # Python
    if any((root / f).exists() for f in ["pyproject.toml", "setup.py", "requirements.txt"]):
        info["languages"].append("Python")
        info["build_system"] = "python/pip"
        if not info["test_cmd"]:
            info["test_cmd"] = "pytest"
        if not info["lint_cmd"]:
            info["lint_cmd"] = "ruff check"

    # Go
    go_mod = root / "go.mod"
    if go_mod.exists():
        info["languages"].append("Go")
        info["build_system"] = "go"
        info["test_cmd"] = "go test ./..."
        info["lint_cmd"] = "golangci-lint run"

    # C / C++
    if (root / "CMakeLists.txt").exists():
        info["languages"].append("C/C++")
        info["build_system"] = "cmake"
        info["test_cmd"] = "ctest --output-on-failure"

    return info

def cmd_init(args):
    """Bootstrap initial knowledge base by scanning repository structure."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    MODULES_DIR.mkdir(parents=True, exist_ok=True)

    root = Path.cwd()
    index = load_index()
    ctx = detect_project_context(root)

    # Top level directories
    subsystems = [
        p.name for p in root.iterdir()
        if p.is_dir() and p.name not in IGNORE_DIRS and not p.name.startswith(".")
    ]

    # 1. Architecture Card
    arch_file = KNOWLEDGE_DIR / "architecture.md"
    if not arch_file.exists() or args.force:
        langs = ", ".join(ctx["languages"]) or "Unknown"
        subs_text = "\n".join(
            f"### `{s}/`\n- **Purpose**: Core subsystem for `{s}`.\n- **Key Files**: [Identify main entries]\n- **Dependencies**: [Internal & external]"
            for s in subsystems
        ) if subsystems else "*(Flat repository structure - see root files)*"

        arch_content = f"""# System Architecture & Topology

## Overview
- **Repository**: `{root.name}`
- **Primary Languages**: {langs}
- **Build System**: `{ctx['build_system'] or 'None/Script'}`
- **Entry Points**: {', '.join(f'`{ep}`' for ep in ctx['entry_points']) if ctx['entry_points'] else 'None detected'}

## Subsystems & Topology
{subs_text}

## Data Flow & Invariants
- [Document primary request/event flows and state boundaries here]
"""
        arch_file.write_text(arch_content.strip() + "\n", encoding="utf-8")
        print(f"[GKE] Created {arch_file}")

    # 2. Conventions Card
    conv_file = KNOWLEDGE_DIR / "conventions.md"
    if not conv_file.exists() or args.force:
        conv_content = f"""# Repository Conventions & Invariants

## Core Coding Standards
- **Language / Style**: Idiomatic {', '.join(ctx['languages']) if ctx['languages'] else 'clean code'}.
- **Error Handling**: Explicit return types and strict checks; never swallow errors silently.
- **Concurrency & Threading**: Clear mutex/lock ownership; avoid locking across heavy I/O boundaries.

## Architectural Boundaries
- Keep business logic decoupled from transport/driver layers.
- Modules communicate via defined interfaces; no circular imports.

## Prohibited Antipatterns
- Never commit secrets, credentials, or unmasked tokens.
- Never add external dependencies without explicit task requirement.
- Never skip error checks on I/O or system calls.
"""
        conv_file.write_text(conv_content.strip() + "\n", encoding="utf-8")
        print(f"[GKE] Created {conv_file}")

    # 3. Test Matrix Card
    test_file = KNOWLEDGE_DIR / "test-matrix.md"
    if not test_file.exists() or args.force:
        test_content = f"""# Test Matrix & Verification Harness

## Test Commands
- **Unit & Integration Suite**: `{ctx['test_cmd'] or 'python scripts/verify.py'}`
- **Linter & Type Checker**: `{ctx['lint_cmd'] or 'tsc --noEmit / ruff check / cargo check'}`
- **Fast Smoke Test**: `{ctx['test_cmd'] or 'npm test'}`

## Verification Requirements
- All tests must pass cleanly (`VERDICT: PASS`).
- Zero warnings or errors from linter/type-checker.
- Any new feature must introduce accompanying tests.
"""
        test_file.write_text(test_content.strip() + "\n", encoding="utf-8")
        print(f"[GKE] Created {test_file}")

    # Register initial cards in index
    index["cards"]["architecture"] = {
        "path": "architecture.md",
        "title": "System Architecture & Topology",
        "tags": ["topology", "subsystems", "architecture", "overview"],
        "summary": f"Subsystems: {', '.join(subsystems) if subsystems else 'single-package'}. Languages: {', '.join(ctx['languages'])}."
    }
    index["cards"]["conventions"] = {
        "path": "conventions.md",
        "title": "Repository Conventions & Invariants",
        "tags": ["conventions", "standards", "error-handling", "antipatterns", "rules"],
        "summary": "Core coding rules, error handling, threading rules, and forbidden antipatterns."
    }
    index["cards"]["test-matrix"] = {
        "path": "test-matrix.md",
        "title": "Test Matrix & Verification Harness",
        "tags": ["tests", "verification", "lint", "commands"],
        "summary": f"Verification commands: {ctx['test_cmd'] or 'standard tests'}, linters: {ctx['lint_cmd']}."
    }

    # Initial file tracking
    for p in root.rglob("*"):
        if p.is_file() and not any(part in IGNORE_DIRS or part.startswith(".") for part in p.parts):
            rel = str(p.relative_to(root)).replace("\\", "/")
            index["tracked_files"][rel] = sha256_file(p)

    save_index(index)
    print(f"[GKE] Initialized Living Knowledge Base in {KNOWLEDGE_DIR}")
    print(f"[GKE] Indexed {len(index['tracked_files'])} repository files.")

def cmd_status(args):
    """Check knowledge base freshness against git and file checksums."""
    if not INDEX_FILE.exists():
        print("[GKE] Error: Knowledge base not initialized. Run 'python scripts/knowledge.py init' first.")
        sys.exit(1)

    index = load_index()
    cards = index.get("cards", {})
    tracked = index.get("tracked_files", {})
    meta = index.get("metadata", {})

    print("==================================================")
    print("      GRAVITAS LIVING KNOWLEDGE BASE STATUS       ")
    print("==================================================")
    print(f"Path: {KNOWLEDGE_DIR}")
    print(f"Last Synchronized: {meta.get('last_updated', 'Unknown')}")
    print(f"Registered Knowledge Cards: {len(cards)}")
    for cid, cdata in cards.items():
        cp = KNOWLEDGE_DIR / cdata["path"]
        status = "OK" if cp.exists() else "MISSING"
        print(f"  [{status}] {cid:15} : {cdata.get('title')} ({', '.join(cdata.get('tags', []))})")

    # Detect git changes
    stale_files = []
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if res.returncode == 0:
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            for l in lines:
                fpath = l[3:].strip().replace("\\", "/")
                stale_files.append((l[:2], fpath))
    except Exception:
        pass

    print(f"\nTracked Files in Index: {len(tracked)}")
    if stale_files:
        print(f"\n[!] Detected {len(stale_files)} uncommitted/modified files:")
        for status_code, fpath in stale_files[:12]:
            print(f"  {status_code} {fpath}")
        if len(stale_files) > 12:
            print(f"  ... and {len(stale_files) - 12} more files.")
        print("\nAction Required: Run 'python scripts/knowledge.py update' after modifications.")
        if args.check:
            sys.exit(1)
    else:
        print("\n[OK] Knowledge Base is fully synchronized with git working tree.")

def cmd_query(args):
    """Query cards by search terms or dump all summaries."""
    if not INDEX_FILE.exists():
        print("[GKE] Knowledge base not initialized.")
        return

    index = load_index()
    cards = index.get("cards", {})
    query = (args.query or "").lower().strip()
    words = query.split()

    matches = []
    for cid, cdata in cards.items():
        haystack = f"{cid} {cdata.get('title','')} {cdata.get('summary','')} {' '.join(cdata.get('tags',[]))}".lower()
        score = sum(1 for w in words if w in haystack) if words else 1
        if score > 0 or not words:
            matches.append((score, cid, cdata))

    matches.sort(key=lambda x: x[0], reverse=True)

    if args.format == "prompt":
        # Compact XML format ideal for injecting into agent prompts
        print("<gravitas_knowledge_context>")
        for _, cid, cdata in matches:
            cp = KNOWLEDGE_DIR / cdata.get("path")
            content = cp.read_text(encoding="utf-8") if cp.exists() else ""
            print(f'<card id="{cid}" title="{cdata.get("title")}">\n{content.strip()}\n</card>')
        print("</gravitas_knowledge_context>")
        return

    print(f"=== Knowledge Base Query: '{query or '*'}' ({len(matches)} results) ===")
    for score, cid, cdata in matches:
        print(f"\nCard: [{cid}] {cdata.get('title')}")
        print(f"Tags: {', '.join(cdata.get('tags', []))}")
        print(f"Summary: {cdata.get('summary')}")
        print(f"File: {KNOWLEDGE_DIR / cdata.get('path')}")
        if args.verbose:
            cp = KNOWLEDGE_DIR / cdata.get("path")
            if cp.exists():
                lines = cp.read_text(encoding="utf-8").splitlines()
                print("Content:")
                for l in lines[:20]:
                    print(f"  {l}")
                if len(lines) > 20:
                    print(f"  ... ({len(lines)-20} more lines)")

def cmd_update(args):
    """Synchronize file hashes and update knowledge base after changes."""
    if not INDEX_FILE.exists():
        print("[GKE] Initializing knowledge base first...")
        cmd_init(args)
        return

    index = load_index()
    root = Path.cwd()
    changed_files = []

    if args.files:
        changed_files = [f.strip() for f in args.files.split(",") if f.strip()]
    else:
        # Check git status
        try:
            res = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True)
            if res.returncode == 0:
                changed_files = [l.strip() for l in res.stdout.splitlines() if l.strip()]
        except Exception:
            pass

    print(f"[GKE] Synchronizing {len(changed_files)} changed files into Knowledge Base...")
    for f in changed_files:
        fp = root / f
        rel = str(fp.relative_to(root) if fp.is_absolute() else fp).replace("\\", "/")
        if fp.exists() and fp.is_file():
            index.setdefault("tracked_files", {})[rel] = sha256_file(fp)
            print(f"  [UPDATED] {rel}")
        elif not fp.exists() and rel in index.get("tracked_files", {}):
            del index["tracked_files"][rel]
            print(f"  [REMOVED] {rel}")

    save_index(index)
    print(f"[GKE] Knowledge Base synchronized successfully. Total tracked: {len(index.get('tracked_files', {}))}")

def cmd_add_card(args):
    """Create or register a new knowledge card for a module or subsystem."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    MODULES_DIR.mkdir(parents=True, exist_ok=True)

    index = load_index()
    cid = args.id.lower().strip()
    cfile = MODULES_DIR / f"{cid}.md"
    rel_path = f"modules/{cid}.md"

    if not cfile.exists() or args.force:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else [cid]
        content = f"""# Module Knowledge Card: {args.title}

## Purpose & Scope
- **Module ID**: `{cid}`
- **Subsystem**: `{args.subsystem or cid}`
- **Summary**: {args.summary or '[Describe module responsibility]'}

## Key Files & Entry Points
- [Add files belonging to this module]

## Invariants & Design Rules
- [Add critical design invariants, thread constraints, or validation rules]

## Verification
- Command: `{args.test_cmd or 'python scripts/verify.py'}`
"""
        cfile.write_text(content.strip() + "\n", encoding="utf-8")
        print(f"[GKE] Created card at {cfile}")

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else [cid]
    index.setdefault("cards", {})[cid] = {
        "path": rel_path,
        "title": args.title,
        "tags": tags,
        "summary": args.summary or f"Knowledge card for {cid}"
    }
    save_index(index)
    print(f"[GKE] Registered card '{cid}' in index.json")

def main():
    parser = argparse.ArgumentParser(description="Gravitas Living Knowledge Engine (GKE)")
    sub = parser.add_subparsers(dest="cmd")

    # init
    p_init = sub.add_parser("init", help="Bootstrap repository knowledge base")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing template cards")

    # status
    p_stat = sub.add_parser("status", help="Show knowledge base freshness and coverage")
    p_stat.add_argument("--check", action="store_true", help="Exit code 1 if stale or unindexed changes exist")

    # query
    p_query = sub.add_parser("query", help="Query knowledge cards by keyword or tags")
    p_query.add_argument("query", nargs="?", default="", help="Search terms")
    p_query.add_argument("--verbose", "-v", action="store_true", help="Show card preview lines")
    p_query.add_argument("--format", choices=["text", "prompt"], default="text", help="Output format ('prompt' formats compact XML)")

    # update
    p_upd = sub.add_parser("update", help="Update tracking hashes and sync cards after code edits")
    p_upd.add_argument("--files", help="Comma-separated list of modified files")

    # add-card
    p_add = sub.add_parser("add-card", help="Create and register a new domain knowledge card")
    p_add.add_argument("--id", required=True, help="Unique card ID (e.g. auth, db-driver, scanner)")
    p_add.add_argument("--title", required=True, help="Human-readable title")
    p_add.add_argument("--tags", default="", help="Comma-separated tags")
    p_add.add_argument("--summary", default="", help="One-line summary")
    p_add.add_argument("--subsystem", default="", help="Subsystem name")
    p_add.add_argument("--test-cmd", default="", help="Specific test command")
    p_add.add_argument("--force", action="store_true", help="Overwrite existing card file")

    args = parser.parse_args()

    if args.cmd == "init":
        cmd_init(args)
    elif args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "query":
        cmd_query(args)
    elif args.cmd == "update":
        cmd_update(args)
    elif args.cmd == "add-card":
        cmd_add_card(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
