# Marko — Microservice de gestion des identifiants

Le microservice **Marko** génère et gère les identifiants physiques associés aux items (utilisé ici dans le cas du projet Lokio) : **QR codes** et **barcodes**.

Lorsqu'un identifiant de type `qrcode` ou `barcode` est créé via l'API, une image est générée automatiquement et stockée dans le système de fichiers. Ces images peuvent ensuite être imprimées et apposées sur les boîtes pour permettre leur scan.

Le microservice expose une API REST sécurisée par JWT, un honeypot sur `/admin/`, et un serveur MCP permettant aux LLM de créer et consulter les identifiants en langage naturel.

---

## Stack

| Composant | Version |
|---|---|
| Python | 3.12 |
| Django | 6.0 |
| Django REST Framework | 3.16.1 |
| SimpleJWT | 5.5.1 |
| drf-yasg (Swagger) | 1.21.11 |
| qrcode | 8.2 |
| python-barcode | 0.16.1 |
| Pillow | 12.0.0 |
| FastMCP | — |
| Gunicorn | — |

---

## Installation

### Avec Docker (recommandé)

**Prérequis :** Docker et Docker Compose installés.

```bash
./deploy.sh
```

Le script `deploy.sh` fait tout automatiquement :

1. Vérifie que Docker est disponible
2. Crée le `.env` depuis `.env.example` si absent et ouvre l'éditeur pour le remplir
3. Valide que `DJANGO_SECRET_KEY` et `DJANGO_SUPERUSER_PASSWORD` sont bien définies
4. Build l'image et démarre les conteneurs (`marko` + `marko-mcp`)
5. Applique les migrations Django
6. Crée le superutilisateur (ignoré s'il existe déjà)
7. Attend que les services soient sains et affiche les URLs

Pour arrêter les services :

```bash
docker compose down
```

---

### Sans Docker (développement local)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd marko
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8003
```

L'API est accessible sur `http://localhost:8003`.

---

## Variables d'environnement

| Variable | Description | Exemple |
|---|---|---|
| `DJANGO_SECRET_KEY` | Clé secrète Django | — |
| `DJANGO_DEBUG` | Mode debug | `false` |
| `DJANGO_ALLOWED_HOSTS` | Hosts autorisés | `localhost,127.0.0.1` |
| `DJANGO_ADMIN_URL` | URL secrète de la vraie interface admin | `mon-panneau-secret` |
| `DJANGO_SUPERUSER_USERNAME` | Login du superutilisateur | `admin` |
| `DJANGO_SUPERUSER_EMAIL` | Email du superutilisateur | `admin@example.com` |
| `DJANGO_SUPERUSER_PASSWORD` | Mot de passe du superutilisateur | — |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Durée du token d'accès (minutes) | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Durée du token de rafraîchissement (jours) | `7` |
| `HONEYPOT_API_KEY` | Clé pour protéger `GET /api/honeypot/` | — |
| `GUNICORN_WORKERS` | Nombre de workers Gunicorn | `3` |
| `GUNICORN_TIMEOUT` | Timeout des requêtes (secondes) | `30` |
| `HOST_PORT` | Port exposé pour l'API | `8003` |
| `MCP_PORT` | Port interne du serveur MCP | `9000` |
| `MCP_HOST_PORT` | Port exposé pour le serveur MCP | `9005` |
| `MCP_API_KEY` | Clé optionnelle pour sécuriser l'accès MCP | — |

---

## Endpoints API

### Types d'identifiants (TypeId)

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/api/typeids/` | Liste les types (`qrcode`, `barcode`, …) |
| `POST` | `/api/typeids/` | Crée un type |
| `GET` | `/api/typeids/{id}/` | Détail d'un type |
| `PUT` / `PATCH` | `/api/typeids/{id}/` | Modifie un type |
| `DELETE` | `/api/typeids/{id}/` | Supprime un type (protégé pour `qrcode` et `barcode`) |

### Identifiants (Identifier)

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/api/identifiers/` | Liste les identifiants (filtre : `?id_item=<id>`) |
| `POST` | `/api/identifiers/` | Crée un identifiant (génère l'image si type qrcode/barcode) |
| `GET` | `/api/identifiers/{id}/` | Détail d'un identifiant |
| `PUT` / `PATCH` | `/api/identifiers/{id}/` | Modifie un identifiant |
| `DELETE` | `/api/identifiers/{id}/` | Supprime un identifiant |

### Authentification JWT

| Méthode | URL | Description |
|---|---|---|
| `POST` | `/api/token/` | Obtenir un token |
| `POST` | `/api/token/refresh/` | Rafraîchir un token |

### Sécurité — Honeypot

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/api/honeypot/` | Liste les tentatives enregistrées |

> Protégé par l'en-tête `X-Honeypot-Key: <HONEYPOT_API_KEY>`.

---

## Documentation interactive

| Interface | URL |
|---|---|
| Swagger UI | `http://localhost:8003/swagger/` |
| ReDoc | `http://localhost:8003/redoc/` |
| JSON (OpenAPI) | `http://localhost:8003/swagger.json` |

---

## Sécurité — Honeypot

L'URL `/admin/` est un honeypot : fausse page de connexion Django qui enregistre chaque tentative (IP, User-Agent, identifiants, horodatage) en base de données et dans `honeypot.log`.

La vraie interface d'administration est disponible à l'URL définie dans `DJANGO_ADMIN_URL`.

```bash
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

---

## Génération des images

Lorsqu'un `Identifier` est créé avec le type `qrcode` ou `barcode`, un signal Django déclenche automatiquement la génération de l'image correspondante :

- **QR code** → encode `https://example.com/<id_item>` (URL à adapter)
- **Barcode** → encode `<id_item>` au format Code128

Les images sont stockées dans `media/identifiers/` et accessibles via `/media/identifiers/<filename>`.

> En production, le dossier `media/` est persisté dans le volume Docker `marko_media`.

---

## Serveur MCP

Accessible via SSE sur `http://localhost:9005/sse` (avec Docker).

### Outils disponibles

| Outil | Description |
|---|---|
| `list_typeids` | Liste les types d'identifiants |
| `get_typeid` | Détail d'un type |
| `create_typeid` | Crée un type |
| `delete_typeid` | Supprime un type |
| `list_identifiers` | Liste les identifiants (filtre optionnel par item) |
| `get_identifier` | Détail d'un identifiant |
| `create_identifier` | Crée un identifiant (génère l'image automatiquement) |
| `delete_identifier` | Supprime un identifiant |
| `get_honeypot_attempts` | Liste les tentatives honeypot |

### Configurer le client MCP

```json
{
  "mcpServers": {
    "marko": {
      "type": "sse",
      "url": "http://localhost:9005/sse"
    }
  }
}
```

---

## Tests

```bash
cd marko
python manage.py test api.tests --verbosity=2
```

Tests unitaires couvrant :

- `TypeIdTests` : list, create, duplicate, retrieve (404), update, partial_update, delete, protection de `qrcode`/`barcode`
- `IdentifierTests` : list, filtrage par `id_item`, create, type invalide, valeur dupliquée, retrieve (404), partial_update, delete

---

## Linter

```bash
ruff check marko/
```

---

## Auteur

Projet **Lokio** — développé par **Clément Chermeux**.

---

## Améliorations futures

- [ ] Authentification sur les endpoints MCP via `MCP_API_KEY`
- [ ] Personnaliser l'URL encodée dans le QR code (depuis `.env` ou la requête)
- [ ] Changer le lieu d'enregistrement des images et sécuriser cette partie
- [ ] Support d'autres formats de codes (EAN-13, DataMatrix, NFC, RFID…)
- [ ] Endpoint pour re-générer une image sans recréer l'identifiant
- [ ] Export CSV / JSON des tentatives honeypot
- [ ] Cohérence des données si un item (Boxify) est supprimé
- [ ] Migration vers PostgreSQL pour la production
- [ ] Mise en place du CI/CD
- [ ] Système de connexion commune Lokio (Keycloak)
- [ ] coherence des données si un proprietaire n'existe plus
- [ ] Instaurer un système de différents droits en fonction des utilisateurs
- [ ] Rajouter système de bande cookie etc pour être aux normes

