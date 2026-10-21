#!/usr/bin/env python3
"""Gravitas project detector for Claude Code.

Detects project language, framework, test runner, and config.
Outputs JSON for agent consumption.
"""
import json
import os
import sys
from pathlib import Path

LANGUAGE_MARKERS = {
    "typescript": ["tsconfig.json", "package.json"],
    "python": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "poetry.lock"],
    "rust": ["Cargo.toml"],
    "go": ["go.mod"],
    "cpp": ["CMakeLists.txt", "Makefile", "*.vcxproj"],
    "csharp": ["*.csproj", "*.sln"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "ruby": ["Gemfile"],
    "php": ["composer.json"],
}

TEST_COMMANDS = {
    "typescript": [
        ("vitest", "npx vitest run"),
        ("jest", "npx jest"),
        ("npm", "npm test -- --passWithNoTests"),
    ],
    "python": [
        ("pytest", "python -m pytest -v"),
        ("unittest", "python -m unittest"),
    ],
    "rust": [
        ("cargo", "cargo test"),
    ],
    "go": [
        ("go", "go test ./..."),
    ],
    "cpp": [
        ("ctest", "ctest --output-on-failure"),
    ],
}

def detect_language(root: Path) -> str:
    for lang, markers in LANGUAGE_MARKERS.items():
        for marker in markers:
            if marker.startswith("*"):
                ext = marker[1:]
                if list(root.glob(f"*{ext}")):
                    return lang
            elif (root / marker).exists():
                return lang
    return "unknown"

def detect_test_command(root: Path, lang: str) -> str:
    if lang == "typescript" or lang == "javascript":
        pkg = root / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text(encoding="utf-8"))
                scripts = data.get("scripts", {})
                if "test" in scripts:
                    return "npm test"
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "vitest" in deps:
                    return "npx vitest run"
                if "jest" in deps:
                    return "npx jest"
            except Exception:
                pass
    elif lang == "python":
        if (root / "pytest.ini").exists() or (root / "conftest.py").exists() or (root / "tests").exists():
            return "python -m pytest -v"
    elif lang == "rust":
        if (root / "Cargo.toml").exists():
            return "cargo test"
    elif lang == "go":
        if (root / "go.mod").exists():
            return "go test ./..."
    elif lang == "cpp":
        if (root / "CMakeLists.txt").exists():
            return "ctest --output-on-failure"

    candidates = TEST_COMMANDS.get(lang, [])
    return candidates[0][1] if candidates else "echo 'No test command detected'"

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    lang = detect_language(root)
    cmd = detect_test_command(root, lang)
    result = {
        "root": str(root),
        "language": lang,
        "test_command": cmd,
        "has_tests": bool(list(root.glob("*test*")) or list(root.glob("*spec*"))),
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
