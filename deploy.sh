#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# deploy.sh — Déploiement du microservice marko
# Usage : ./deploy.sh
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
ENV_EXAMPLE="$SCRIPT_DIR/.env.example"

# ── Couleurs ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*" >&2; }

# ── Vérification des prérequis ────────────────────────────────────────────────
info "Vérification des prérequis..."

if ! command -v docker &>/dev/null; then
    error "Docker n'est pas installé."
    exit 1
fi

if ! docker compose version &>/dev/null; then
    error "Docker Compose (plugin) n'est pas disponible."
    exit 1
fi

success "Docker $(docker --version | awk '{print $3}' | tr -d ',')"

# ── Gestion du fichier .env ───────────────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
    if [ ! -f "$ENV_EXAMPLE" ]; then
        error ".env.example introuvable. Impossible de continuer."
        exit 1
    fi

    info "Création du fichier .env depuis .env.example..."
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    success ".env créé."

    info "Ouverture de l'éditeur — remplissez les valeurs puis sauvegardez et quittez."
    EDITOR="${EDITOR:-nano}"
    "$EDITOR" "$ENV_FILE"

    echo ""
    read -rp "$(echo -e "${BLUE}[INFO]${NC} Continuer le déploiement ? [O/n] ")" CONFIRM
    if [[ "${CONFIRM,,}" == "n" ]]; then
        warn "Déploiement annulé. Le fichier .env a été conservé."
        exit 0
    fi
else
    info "Fichier .env trouvé — déploiement automatique."
fi

# ── Vérification des variables critiques ─────────────────────────────────────
source "$ENV_FILE"

if [[ -z "${DJANGO_SECRET_KEY:-}" ]] || [[ "$DJANGO_SECRET_KEY" == "changeme-generate-a-real-secret-key" ]]; then
    error "DJANGO_SECRET_KEY non définie ou non modifiée dans .env"
    error "Générez une clé avec : python -c \"import secrets; print(secrets.token_urlsafe(50))\""
    exit 1
fi

if [[ -z "${DJANGO_SUPERUSER_PASSWORD:-}" ]] || [[ "$DJANGO_SUPERUSER_PASSWORD" == "changeme-strong-password" ]]; then
    error "DJANGO_SUPERUSER_PASSWORD non définie ou non modifiée dans .env"
    exit 1
fi

# ── Build & déploiement ───────────────────────────────────────────────────────
cd "$SCRIPT_DIR"

info "Construction de l'image Docker..."
docker compose build --no-cache

info "Arrêt du conteneur existant (si présent)..."
docker compose down --remove-orphans || true

info "Démarrage du service..."
docker compose up -d

# ── Vérification du démarrage ─────────────────────────────────────────────────
info "Attente du démarrage du conteneur..."
MAX_WAIT=30
WAITED=0
until docker compose ps | grep -q "healthy\|running"; do
    sleep 2
    WAITED=$((WAITED + 2))
    if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        warn "Le conteneur met du temps à démarrer. Vérifiez les logs :"
        docker compose logs --tail=30
        break
    fi
done

# ── Migrations & superutilisateur ────────────────────────────────────────────
info "Application des migrations Django..."
docker compose exec marko python manage.py migrate --noinput

info "Création du superutilisateur (ignoré s'il existe déjà)..."
docker compose exec marko python manage.py createsuperuser --noinput 2>/dev/null \
    && success "Superutilisateur « ${DJANGO_SUPERUSER_USERNAME:-admin} » créé." \
    || warn "Le superutilisateur existe déjà ou DJANGO_SUPERUSER_* non définis — aucune action."

# ── Résumé ────────────────────────────────────────────────────────────────────
HOST_PORT="${HOST_PORT:-8003}"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
success "Déploiement terminé !"
echo ""
echo -e "  API      : ${BLUE}http://localhost:${HOST_PORT}/api/identifiers/${NC}"
echo -e "  Swagger  : ${BLUE}http://localhost:${HOST_PORT}/swagger/${NC}"
echo -e "  ReDoc    : ${BLUE}http://localhost:${HOST_PORT}/redoc/${NC}"
echo ""
echo -e "  Logs     : docker compose logs -f"
echo -e "  Arrêter  : docker compose down"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
