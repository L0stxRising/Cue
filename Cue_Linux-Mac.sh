#!/bin/bash
# Launches For Linux and Mac!!!
DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/Env"
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"
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

if [ ! -f "$PY" ]; then
    if [ -d "$VENV" ]; then
        echo -e "${Y}⟩${N} Existing environment appears broken or incomplete. Rebuilding..."
        rm -rf "$VENV"
    else
        echo -e "${Y}⟩${N} Creating Python virtual environment..."
    fi

    if command -v python3 >/dev/null 2>&1; then
        SYS_PY="python3"
    elif command -v python >/dev/null 2>&1; then
        SYS_PY="python"
    else
        echo -e "${R}✗ Python not found! Please install Python 3.10+${N}"
        exit 1
    fi

    "$SYS_PY" -m venv "$VENV" || {
        echo -e "${R}✗ Failed to create venv. (On Ubuntu/Debian, try: sudo apt install python3-venv)${N}"
        exit 1
    }

    if [ -f "$DIR/requirements.txt" ]; then
        echo -e "${Y}⟩${N} Installing dependencies from requirements.txt..."
        "$PIP" install --upgrade pip -q
        "$PIP" install -r "$DIR/requirements.txt" -q || { echo -e "${R}✗ Dependency installation failed.${N}"; exit 1; }
        echo -e "${G}✓${N} Environment setup complete."
    else
        echo -e "${R}✗ requirements.txt not found! Expected at $DIR/requirements.txt${N}"
        exit 1
    fi
fi

if [ ! -f "$PY" ]; then
    echo -e "${R}✗ Python not found at $PY. Environment creation may have failed.${N}"
    exit 1
fi

mkdir -p "$DIR/tmp"
mkdir -p "$DIR/Output"

get_saved_key() {
    if [ -f "$ENV_FILE" ]; then
        grep "OPENROUTER_API_KEY=" "$ENV_FILE" | cut -d '=' -f2-
    fi
}
save_key() {
    cat > "$ENV_FILE" <<EOF
OPENROUTER_API_KEY=$1
EOF
    chmod 600 "$ENV_FILE"
}

CURRENT_KEY="$(get_saved_key || true)"
STATUS="INVALID"
if [ -n "$CURRENT_KEY" ]; then
    STATUS="$("$PY" "$DIR/test_api_key.py" "$CURRENT_KEY" 2>/dev/null || true)"
fi

while [ "$STATUS" != "VALID" ]; do
    echo -e "${M}┌──────────────────────────────────────┐${N}"
    echo -e "${M}│${W} OpenRouter API Key Required/Invalid${M}  │${N}"
    echo -e "${M}└──────────────────────────────────────┘${N}"
    read -rp $'\033[33m⟩ \033[0mPaste your API key (or Q to quit): ' API_KEY
    if [[ "$API_KEY" =~ ^[Qq]$ ]]; then
        echo "Exiting."
        exit 0
    fi
    echo -e "${D}Validating...${N}"
    STATUS="$("$PY" "$DIR/test_api_key.py" "$API_KEY" 2>/dev/null || true)"
    if [ "$STATUS" == "VALID" ]; then
        save_key "$API_KEY"
        echo -e "${G}✓${N} API key validated and saved."
    else
        echo -e "${R}✗ Key rejected (${STATUS:-no response}). Try again.${N}"
    fi
done

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
    pkexec env \
        SUDO_USER="$CURRENT_USER" \
        DISPLAY="$DISPLAY" \
        XAUTHORITY="$XAUTHORITY" \
        WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
        "$PY" "$DIR/handler.py" "$ARG"
    PKEXEC_RESULT=$?

    if [ $PKEXEC_RESULT -ne 0 ]; then
        echo -e "${Y}⟩${N} pkexec failed, trying password prompt fallback..."
        if command -v zenity >/dev/null 2>&1; then
            SUDO_PASS=$(zenity --password --title="Cue — Authentication Required") || exit 1
        elif command -v kdialog >/dev/null 2>&1; then
            SUDO_PASS=$(kdialog --password "Enter your password to run Cue:") || exit 1
        else
            read -rsp $'\033[33m⟩ \033[0mSudo password: ' SUDO_PASS
            echo ""
        fi
        echo "$SUDO_PASS" | sudo -S -v 2>/dev/null || { echo -e "${R}✗ Incorrect password.${N}"; unset SUDO_PASS; exit 1; }
        unset SUDO_PASS
        exec sudo -E "$PY" "$DIR/handler.py" "$ARG"
    fi

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