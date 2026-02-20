#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

log() { printf "\n[init] %s\n" "$*"; }

detect_pkg_manager() {
  if command -v apt-get >/dev/null 2>&1; then echo "apt"
  elif command -v dnf >/dev/null 2>&1; then echo "dnf"
  elif command -v yum >/dev/null 2>&1; then echo "yum"
  elif command -v pacman >/dev/null 2>&1; then echo "pacman"
  elif command -v zypper >/dev/null 2>&1; then echo "zypper"
  elif command -v apk >/dev/null 2>&1; then echo "apk"
  else echo "unknown"
  fi
}

install_python_deps() {
  local pm="$1"

  case "$pm" in
    apt)
      sudo apt-get update
      sudo apt-get install -y python3 python3-pip python3-venv
      ;;
    dnf)
      sudo dnf install -y python3 python3-pip
      ;;
    yum)
      sudo yum install -y python3 python3-pip
      ;;
    pacman)
      sudo pacman -Sy --noconfirm python python-pip
      ;;
    zypper)
      sudo zypper --non-interactive install python3 python3-pip
      ;;
    apk)
      sudo apk add --no-cache python3 py3-pip
      ;;
    *)
      echo "Distribuição não suportada automaticamente."
      echo "Instale manualmente: python3 + pip + venv."
      exit 1
      ;;
  esac
}

log "Detectando distribuição Linux..."
DISTRO_ID="unknown"
DISTRO_LIKE="unknown"

if [[ -f /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
  DISTRO_ID="${ID:-unknown}"
  DISTRO_LIKE="${ID_LIKE:-unknown}"
fi

log "ID=${DISTRO_ID} | ID_LIKE=${DISTRO_LIKE}"

PM="$(detect_pkg_manager)"
log "Gerenciador detectado: ${PM}"
install_python_deps "$PM"

if [[ ! -d ".venv" ]]; then
  log "Criando ambiente virtual..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

log "Atualizando pip e instalando dependências..."
python -m pip install --upgrade pip
pip install -r requirements.txt

log "Executando parser..."
python parser_filmow.py