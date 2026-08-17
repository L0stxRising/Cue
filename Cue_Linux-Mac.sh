set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/Env"
PY="$VENV/bin/python"
ENV_FILE="$DIR/.env"

C="\033[36m"  B="\033[34m"  M="\033[35m"  G="\033[32m"
Y="\033[33m"  R="\033[31m"  W="\033[1;37m"  D="\033[2m"  N="\033[0m"

echo ""
echo -e "${C}   ██████╗ ${B}██╗   ██╗${M}███████╗${N}"
echo -e "${C}  ██╔════╝ ${B}██║   ██║${M}██╔════╝${N}"
echo -e "${C}  ██║      ${B}██║   ██║${M}█████╗  ${N}"
echo -e "${C}  ██║      ${B}██║   ██║${M}██╔══╝  ${N}"
echo -e "${C}  ╚██████╗ ${B}╚██████╔╝${M}███████╗${N}"
echo -e "${C}   ╚═════╝  ${B}╚═════╝ ${M}╚══════╝${N}"
echo -e "${D}  Screenshot → Guide Maker${N}"
echo ""

if [ ! -f "$ENV_FILE" ] || ! grep -q "OPENROUTER_API_KEY=." "$ENV_FILE" 2>/dev/null; then
    echo -e "${M}┌──────────────────────────────────────┐${N}"
    echo -e "${M}│${W}   OpenRouter API Key Required        ${M}│${N}"
    echo -e "${M}└──────────────────────────────────────┘${N}"
    read -rp $'\033[33m⟩ \033[0mPaste your API key: ' API_KEY
    cat > "$ENV_FILE" <<EOF
# CUE Configuration — Auto-generated
# DO NOT share this file or commit it to version control!
OPENROUTER_API_KEY=$API_KEY
EOF
    chmod 600 "$ENV_FILE"
    echo -e "${G}✓${N} API key saved to .env"
    echo ""
fi

echo -e "${B}┌──────────────────────────────────────┐${N}"
echo -e "${B}│${W}          Select Mode                 ${B}│${N}"
echo -e "${B}├──────────────────────────────────────┤${N}"
echo -e "${B}│${N}   ${C}1)${N} CLI  — Terminal interface       ${B}│${N}"
echo -e "${B}│${N}   ${M}2)${N} GUI  — Graphical interface      ${B}│${N}"
echo -e "${B}└──────────────────────────────────────┘${N}"
read -rp $'\033[33m⟩ \033[0mChoice [1/2]: ' MODE

case "$MODE" in
    2|gui|GUI) ARG="gui" ;;
    *)         ARG="cli" ;;
esac

CURRENT_USER="$(id -un)"

echo -e "${Y}⟩${N} Requesting elevated privileges..."

if [[ "$(uname)" == "Darwin" ]]; then
    ESCAPED_CMD="SUDO_USER=${CURRENT_USER} '${PY}' '${DIR}/handler.py' ${ARG}"
    osascript -e "do shell script \"${ESCAPED_CMD}\" with administrator privileges" \
        || { echo -e "${R}✗ Authentication failed or cancelled.${N}"; exit 1; }

elif command -v pkexec >/dev/null 2>&1; then
    exec pkexec env \
        SUDO_USER="$CURRENT_USER" \
        DISPLAY="$DISPLAY" \
        XAUTHORITY="$XAUTHORITY" \
        WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
        "$PY" "$DIR/handler.py" "$ARG"

elif command -v zenity >/dev/null 2>&1; then
    SUDO_PASS=$(zenity --password --title="Cue — Authentication Required") || exit 1
    echo "$SUDO_PASS" | sudo -S -v 2>/dev/null || { echo -e "${R}✗ Incorrect password.${N}"; unset SUDO_PASS; exit 1; }
    unset SUDO_PASS
    exec sudo -E "$PY" "$DIR/handler.py" "$ARG"

elif command -v kdialog >/dev/null 2>&1; then
    SUDO_PASS=$(kdialog --password "Enter your password to run Cue:") || exit 1
    echo "$SUDO_PASS" | sudo -S -v 2>/dev/null || { echo -e "${R}✗ Incorrect password.${N}"; unset SUDO_PASS; exit 1; }
    unset SUDO_PASS
    exec sudo -E "$PY" "$DIR/handler.py" "$ARG"

else
    read -rsp $'\033[33m⟩ \033[0mSudo password: ' SUDO_PASS
    echo ""
    echo "$SUDO_PASS" | sudo -S -v 2>/dev/null || { echo -e "${R}✗ Incorrect password.${N}"; unset SUDO_PASS; exit 1; }
    unset SUDO_PASS
    exec sudo -E "$PY" "$DIR/handler.py" "$ARG"
fi