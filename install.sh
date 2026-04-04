#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
#  Arch Linux AI Agent — Installer
#  Installs the agent so you can run it by just typing: agent
# ──────────────────────────────────────────────────────────────────────

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

INSTALL_DIR="$HOME/.local/share/arch-agent"
BIN_DIR="$HOME/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       Arch Linux AI Agent — Installer                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── 1. Check Python ─────────────────────────────────────────────────
echo -e "${CYAN}[1/4]${NC} Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}✗ Python 3 not found. Install it: sudo pacman -S python${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  ${GREEN}✓${NC} Python ${PYTHON_VERSION} found"

# ─── 2. Install to ~/.local/share/arch-agent ─────────────────────────
echo -e "${CYAN}[2/4]${NC} Installing agent to ${DIM}${INSTALL_DIR}${NC}..."

# Clean previous install
rm -rf "${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"

# Copy source files
cp "${SCRIPT_DIR}/agent.py" "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/config.py" "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/router.py" "${INSTALL_DIR}/"
cp -r "${SCRIPT_DIR}/tools" "${INSTALL_DIR}/"

if [ -f "${SCRIPT_DIR}/.env" ]; then
    cp "${SCRIPT_DIR}/.env" "${INSTALL_DIR}/.env"
fi

echo -e "  ${GREEN}✓${NC} Source files copied"

# ─── 3. Install Python dependencies ──────────────────────────────────
echo -e "${CYAN}[3/4]${NC} Installing Python dependencies..."
pip install --user --break-system-packages -q \
    'litellm>=1.40.0' \
    'ollama>=0.2.0' \
    'duckduckgo-search>=6.0.0' \
    'rich>=13.0.0' \
    'pydantic>=2.0.0' 2>/dev/null \
|| pip install --user -q \
    'litellm>=1.40.0' \
    'ollama>=0.2.0' \
    'duckduckgo-search>=6.0.0' \
    'rich>=13.0.0' \
    'pydantic>=2.0.0'

echo -e "  ${GREEN}✓${NC} Dependencies installed"

# ─── 4. Create the 'agent' launcher in ~/.local/bin ───────────────────
echo -e "${CYAN}[4/4]${NC} Creating launcher command..."
mkdir -p "${BIN_DIR}"

cat > "${BIN_DIR}/agent" << 'LAUNCHER'
#!/usr/bin/env bash
# Arch Linux AI Agent launcher
exec python3 "$HOME/.local/share/arch-agent/agent.py" "$@"
LAUNCHER

chmod +x "${BIN_DIR}/agent"
echo -e "  ${GREEN}✓${NC} Created ${DIM}${BIN_DIR}/agent${NC}"

# ─── Check PATH ──────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo -e "${RED}⚠${NC}  ${BIN_DIR} is not in your PATH."
    echo -e "   Add this to your ${BOLD}~/.bashrc${NC} or ${BOLD}~/.zshrc${NC}:"
    echo ""
    echo -e "   ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    echo ""
fi

# ─── Done ─────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}✓ Installation complete!${NC}"
echo ""
echo -e "  Run the agent:  ${CYAN}${BOLD}agent${NC}"
echo -e "  Select model:   ${CYAN}${BOLD}agent --select${NC}"
echo ""
