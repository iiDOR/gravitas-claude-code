#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");

const YES = process.argv.includes("--yes") || process.argv.includes("-y");

const REPO_ROOT = path.join(__dirname, "..");
const CLAUDE_DIR = path.join(os.homedir(), ".claude");
const SKILL_DST = path.join(CLAUDE_DIR, "skills", "gravitas");
const HOOKS_DST = path.join(CLAUDE_DIR, "hooks", "gravitas");
const SETTINGS = path.join(CLAUDE_DIR, "settings.json");

const PYTHON = process.platform === "win32" ? "python" : "python3";
const HOOK_CMD = (name) =>
  `${PYTHON} ${path.join(HOOKS_DST, name).replace(/\\/g, "/")}`;

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

function patchSettings() {
  let settings = {};
  if (fs.existsSync(SETTINGS)) {
    try { settings = JSON.parse(fs.readFileSync(SETTINGS, "utf8")); }
    catch { console.error("  Warning: could not parse settings.json — skipping hook wiring"); return; }
  }

  settings.hooks ??= {};

  const pre = { matcher: "Write|Edit|MultiEdit", hooks: [{ type: "command", command: HOOK_CMD("pre_tool.py"), timeout: 5 }] };
  const post = { matcher: "*", hooks: [{ type: "command", command: HOOK_CMD("post_tool.py"), timeout: 5 }] };
  const stop = { hooks: [{ type: "command", command: HOOK_CMD("stop_gate.py"), timeout: 5 }] };

  const alreadyHas = (arr, cmd) => Array.isArray(arr) && arr.some(e => e.hooks?.some(h => h.command === cmd));

  if (!alreadyHas(settings.hooks.PreToolUse, pre.hooks[0].command)) {
    settings.hooks.PreToolUse = [...(settings.hooks.PreToolUse ?? []), pre];
  }
  if (!alreadyHas(settings.hooks.PostToolUse, post.hooks[0].command)) {
    settings.hooks.PostToolUse = [...(settings.hooks.PostToolUse ?? []), post];
  }
  if (!alreadyHas(settings.hooks.Stop, stop.hooks[0].command)) {
    settings.hooks.Stop = [...(settings.hooks.Stop ?? []), stop];
  }

  fs.writeFileSync(SETTINGS, JSON.stringify(settings, null, 2) + "\n", "utf8");
}

function confirm(msg) {
  if (YES) return true;
  const readline = require("readline").createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(r => readline.question(`${msg} [y/N] `, a => { readline.close(); r(a.trim().toLowerCase() === "y"); }));
}

async function main() {
  console.log("\nGravitas for Claude Code\n");
  console.log("  Skill  →", SKILL_DST);
  console.log("  Hooks  →", HOOKS_DST);
  console.log("  Config →", SETTINGS);
  console.log();

  if (!await confirm("Install?")) { console.log("Aborted."); process.exit(0); }

  console.log("\nCopying skill files...");
  copyDir(path.join(REPO_ROOT, "skill"), SKILL_DST);

  console.log("Copying hook scripts...");
  copyDir(path.join(REPO_ROOT, "hooks"), HOOKS_DST);

  console.log("Patching settings.json...");
  patchSettings();

  console.log("\nDone. Restart Claude Code to activate.\n");
  console.log("Enforces:");
  console.log("  [1] Read-before-write — blocks edits to unread files");
  console.log("  [3] Evidence-backed completion — logs reads/writes/test verdicts");
  console.log("  [4] Stop gate — blocks session end on unresolved failures\n");
}

main().catch(e => { console.error(e.message); process.exit(1); });
