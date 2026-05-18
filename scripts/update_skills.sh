#!/usr/bin/env bash
# ATHOS — skill updater
# Usage: ./update_skills.sh [--dry-run] [--verbose]
# Updates all reference repos, pip packages, npm tools, and codex/claude skills

set -euo pipefail

ATHOS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REFS="$ATHOS_ROOT/skills/references"
# venv312 = Python 3.12, used for agentmemory/chromadb (incompatible with 3.14)
VENV="$ATHOS_ROOT/venv312"
LOG="$ATHOS_ROOT/logs/update_skills_$(date +%Y%m%d_%H%M%S).log"
DRY_RUN=false
VERBOSE=false
ERRORS=()

# Parse flags
for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN=true ;;
    --verbose) VERBOSE=true ;;
  esac
done

mkdir -p "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1

log() { echo "[$(date +%H:%M:%S)] $*"; }
ok()  { echo "  ✓ $*"; }
err() { echo "  ✗ $*"; ERRORS+=("$*"); }
run() { $DRY_RUN && echo "  [dry] $*" || eval "$@"; }

log "═══════════════════════════════════════"
log "ATHOS SKILL UPDATER — $(date '+%Y-%m-%d %H:%M')"
log "dry-run: $DRY_RUN"
log "═══════════════════════════════════════"

# ── 1. Git reference repos ─────────────────────────────────────────────────────
log "▶ Reference repos (git pull)"

# Format: "name|url"
REPOS=(
  # Agent frameworks
  "agent-skills|https://github.com/addyosmani/agent-skills.git"
  "gstack|https://github.com/garrytan/gstack.git"
  "gbrain|https://github.com/garrytan/gbrain.git"
  # UI Components
  "primitives|https://github.com/radix-ui/primitives.git"
  "ui|https://github.com/shadcn-ui/ui.git"
  "material-ui|https://github.com/mui/material-ui.git"
  "chakra-ui|https://github.com/chakra-ui/chakra-ui.git"
  "tailwindcss|https://github.com/tailwindlabs/tailwindcss.git"
  "ui-ux-pro-max-skill|https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git"
  "UI-UX-Roadmap-2024|https://github.com/CIS-Team/UI-UX-Roadmap-2024.git"
  "Front-End-Design-Checklist|https://github.com/thedaviddias/Front-End-Design-Checklist.git"
  # Shopify
  "dawn|https://github.com/Shopify/dawn.git"
  "polaris|https://github.com/Shopify/polaris.git"
  "awesome-shopify|https://github.com/julionc/awesome-shopify.git"
  "shop-app|https://github.com/abdoutech19/shop-app.git"
  # WordPress
  "wprig|https://github.com/wprig/wprig.git"
  # LLM Education
  "dive-into-llms|https://github.com/Lordog/dive-into-llms.git"
)

for entry in "${REPOS[@]}"; do
  name="${entry%%|*}"
  url="${entry##*|}"
  dir="$REFS/$name"
  if [ -d "$dir/.git" ]; then
    log "  $name"
    if $DRY_RUN; then
      echo "  [dry] git -C $dir pull --ff-only --quiet"
    else
      if git -C "$dir" pull --ff-only --quiet 2>/dev/null; then
        ok "$name updated"
      else
        git -C "$dir" fetch --quiet 2>/dev/null && ok "$name fetched (no merge)" || err "$name: pull failed"
      fi
    fi
  else
    log "  $name — not found, cloning…"
    run "git clone --depth=1 '$url' '$dir'" && ok "$name cloned" || err "$name: clone failed"
  fi
done

# ── 2. Python packages in ATHOS venv ──────────────────────────────────────────
log "▶ Python packages (pip upgrade)"
PY_PACKAGES=(agentmemory openai anthropic psutil httpx)

source "$VENV/bin/activate" 2>/dev/null || { err "venv not found at $VENV"; }

for pkg in "${PY_PACKAGES[@]}"; do
  log "  $pkg"
  run "pip install --upgrade --quiet '$pkg' 2>/dev/null" && ok "$pkg" || err "$pkg: upgrade failed"
done

deactivate 2>/dev/null || true

# ── 3. gstack rebuild (si modifié) ────────────────────────────────────────────
log "▶ gstack rebuild"
GSTACK_DIR="$REFS/gstack"
if [ -d "$GSTACK_DIR" ]; then
  if $DRY_RUN; then
    echo "  [dry] bash $GSTACK_DIR/setup"
  else
    export PATH="$HOME/.bun/bin:$PATH"
    bash "$GSTACK_DIR/setup" 2>/dev/null && ok "gstack rebuilt" || err "gstack: setup failed"
  fi
fi

# ── 4. gbrain update ──────────────────────────────────────────────────────────
log "▶ gbrain skillpack update"
GBRAIN_DIR="$REFS/gbrain"
if [ -d "$GBRAIN_DIR" ]; then
  if $DRY_RUN; then
    echo "  [dry] gbrain skillpack install --all"
  else
    export PATH="$HOME/.bun/bin:$PATH"
    cd "$GBRAIN_DIR" && bun run src/cli.ts skillpack install --all 2>/dev/null && ok "gbrain skillpacks updated" || err "gbrain: skillpack failed"
  fi
fi

# ── 5. agent-skills symlinks refresh ──────────────────────────────────────────
log "▶ agent-skills symlinks"
AGENT_SKILLS_DIR="$REFS/agent-skills/skills"
CODEX_SKILLS_DIR="$HOME/.codex/skills"
if [ -d "$AGENT_SKILLS_DIR" ]; then
  for skill_dir in "$AGENT_SKILLS_DIR"/*/; do
    name=$(basename "$skill_dir")
    target="$CODEX_SKILLS_DIR/$name"
    if [ ! -e "$target" ]; then
      $DRY_RUN && echo "  [dry] ln -s $skill_dir $target" || ln -s "$skill_dir" "$target"
      ok "linked: $name"
    fi
  done
fi

# ── 6. npm global tools ────────────────────────────────────────────────────────
log "▶ npm global tools"
NPM_TOOLS=(9router)

for tool in "${NPM_TOOLS[@]}"; do
  log "  $tool"
  run "npm install -g '$tool' --silent 2>/dev/null" && ok "$tool" || err "$tool: npm install failed"
done

# ── 7. Codex skills (~/.codex/skills/) ────────────────────────────────────────
log "▶ Codex skills (git repos only)"
CODEX_SKILLS="$HOME/.codex/skills"
if [ -d "$CODEX_SKILLS" ]; then
  for skill_dir in "$CODEX_SKILLS"/*/; do
    if [ -d "$skill_dir/.git" ]; then
      name=$(basename "$skill_dir")
      log "  $name"
      run "git -C '$skill_dir' pull --ff-only --quiet 2>/dev/null" && ok "$name" || err "$name: pull failed"
    fi
  done
else
  log "  Codex skills dir not found, skipping"
fi

# ── 8. Claude skills (~/.claude/skills/) ──────────────────────────────────────
log "▶ Claude skills (git repos only)"
CLAUDE_SKILLS="$HOME/.claude/skills"
if [ -d "$CLAUDE_SKILLS" ]; then
  for skill_dir in "$CLAUDE_SKILLS"/*/; do
    if [ -d "$skill_dir/.git" ]; then
      name=$(basename "$skill_dir")
      log "  $name"
      run "git -C '$skill_dir' pull --ff-only --quiet 2>/dev/null" && ok "$name" || err "$name: pull failed"
    fi
  done
else
  log "  Claude skills dir not found, skipping"
fi

# ── Summary ────────────────────────────────────────────────────────────────────
log "═══════════════════════════════════════"
if [ ${#ERRORS[@]} -eq 0 ]; then
  log "✅ All skills updated. Log: $LOG"
else
  log "⚠️  Done with ${#ERRORS[@]} error(s):"
  for e in "${ERRORS[@]}"; do log "   - $e"; done
  log "Log: $LOG"
  exit 1
fi
