#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
#  Arch Linux AI Agent — Uninstaller
# ──────────────────────────────────────────────────────────────────────

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

INSTALL_DIR="$HOME/.local/share/arch-agent"
BIN_FILE="$HOME/.local/bin/agent"

echo -e "${CYAN}${BOLD}Uninstalling Arch Linux AI Agent...${NC}"

if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo -e "  ${GREEN}✓${NC} Removed ${DIM}${INSTALL_DIR}${NC}"
else
    echo -e "  ${DIM}(not found: ${INSTALL_DIR})${NC}"
fi

if [ -f "$BIN_FILE" ]; then
    rm -f "$BIN_FILE"
    echo -e "  ${GREEN}✓${NC} Removed ${DIM}${BIN_FILE}${NC}"
else
    echo -e "  ${DIM}(not found: ${BIN_FILE})${NC}"
fi

echo ""
echo -e "${GREEN}${BOLD}✓ Uninstalled.${NC} Python dependencies were left in place."
echo -e "  To remove them too: ${CYAN}pip uninstall litellm ollama duckduckgo-search rich pydantic${NC}"
