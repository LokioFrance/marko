"""
Serveur MCP pour le microservice Marko.

Expose les outils suivants à tout client MCP (Claude, etc.) :
  - list_typeids          : lister les types d'identifiants
  - get_typeid            : détail d'un type
  - create_typeid         : créer un type
  - delete_typeid         : supprimer un type (protégé pour qrcode/barcode)
  - list_identifiers      : lister les identifiants générés
  - get_identifier        : détail d'un identifiant
  - create_identifier     : créer un identifiant (génère l'image automatiquement)
  - delete_identifier     : supprimer un identifiant
  - get_honeypot_attempts : lister les tentatives enregistrées par le honeypot

Transport : SSE (HTTP) — le serveur écoute sur 0.0.0.0:${MCP_PORT}.

Variables d'environnement :
  MARKO_API_URL    : URL de base de l'API marko (ex: http://marko:8000)
  MCP_PORT         : port d'écoute du serveur MCP (défaut: 9000)
  MCP_API_KEY      : clé partagée attendue dans l'en-tête X-MCP-Key (optionnel)
  HONEYPOT_API_KEY : clé pour accéder à GET /api/honeypot/
"""

import os

import httpx
from mcp.server.fastmcp import FastMCP

# ── Configuration ─────────────────────────────────────────────────────────────

MARKO_API_URL = os.environ.get("MARKO_API_URL", "http://marko:8000").rstrip("/")
MCP_PORT = int(os.environ.get("MCP_PORT", "9000"))
MCP_API_KEY = os.environ.get("MCP_API_KEY", "")
HONEYPOT_API_KEY = os.environ.get("HONEYPOT_API_KEY", "")

mcp = FastMCP(
    name="marko-mcp",
    instructions=(
        "Serveur MCP du microservice Marko. "
        "Permet de gérer les identifiants physiques (QR codes, barcodes) associés aux items Lokio. "
        "TypeId définit le type d'identifiant (qrcode, barcode). "
        "Identifier représente un identifiant généré pour un item précis — "
        "la création d'un Identifier de type qrcode ou barcode génère automatiquement une image. "
        "Donne également accès aux tentatives honeypot enregistrées sur /admin/."
    ),
)


# ── Client HTTP ───────────────────────────────────────────────────────────────

def _client() -> httpx.Client:
    return httpx.Client(base_url=MARKO_API_URL, timeout=10.0)


def _check(response: httpx.Response) -> dict | list | None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise ValueError(
            f"Erreur API {e.response.status_code} : {e.response.text}"
        ) from e
    if response.status_code == 204:
        return None
    return response.json()


# ── OUTILS — TYPE ID ──────────────────────────────────────────────────────────

@mcp.tool()
def list_typeids() -> list:
    """Liste tous les types d'identifiants (qrcode, barcode, etc.)."""
    with _client() as c:
        return _check(c.get("/api/typeids/"))


@mcp.tool()
def get_typeid(typeid_id: int) -> dict:
    """
    Retourne le détail d'un type d'identifiant.

    Args:
        typeid_id: Identifiant du type.
    """
    with _client() as c:
        return _check(c.get(f"/api/typeids/{typeid_id}/"))


@mcp.tool()
def create_typeid(name: str) -> dict:
    """
    Crée un nouveau type d'identifiant.

    Args:
        name: Nom du type (ex: "rfid", "nfc"). Doit être unique.
    """
    with _client() as c:
        return _check(c.post("/api/typeids/", json={"name": name}))


@mcp.tool()
def delete_typeid(typeid_id: int) -> str:
    """
    Supprime un type d'identifiant. Les types 'qrcode' et 'barcode' sont protégés.

    Args:
        typeid_id: Identifiant du type à supprimer.
    """
    with _client() as c:
        _check(c.delete(f"/api/typeids/{typeid_id}/"))
    return f"Type {typeid_id} supprimé."


# ── OUTILS — IDENTIFIER ───────────────────────────────────────────────────────

@mcp.tool()
def list_identifiers(id_item: int | None = None) -> list:
    """
    Liste les identifiants générés. Filtre optionnel par item.

    Args:
        id_item: Identifiant de l'item Lokio (optionnel).
    """
    with _client() as c:
        params = {"id_item": id_item} if id_item else {}
        return _check(c.get("/api/identifiers/", params=params))


@mcp.tool()
def get_identifier(identifier_id: int) -> dict:
    """
    Retourne le détail d'un identifiant.

    Args:
        identifier_id: Identifiant de l'entrée.
    """
    with _client() as c:
        return _check(c.get(f"/api/identifiers/{identifier_id}/"))


@mcp.tool()
def create_identifier(id_type: str, id_item: int, value: str | None = None) -> dict:
    """
    Crée un identifiant pour un item. Si le type est 'qrcode' ou 'barcode',
    une image est générée automatiquement.

    Args:
        id_type: Nom du type (ex: "qrcode", "barcode", "rfid").
        id_item: Identifiant de l'item Lokio auquel l'identifiant est lié.
        value:   Valeur optionnelle (code, URL, texte…).
    """
    payload: dict = {"id_type": id_type, "id_item": id_item}
    if value:
        payload["value"] = value
    with _client() as c:
        return _check(c.post("/api/identifiers/", json=payload))


@mcp.tool()
def delete_identifier(identifier_id: int) -> str:
    """
    Supprime un identifiant et son image associée.

    Args:
        identifier_id: Identifiant de l'entrée à supprimer.
    """
    with _client() as c:
        _check(c.delete(f"/api/identifiers/{identifier_id}/"))
    return f"Identifiant {identifier_id} supprimé."


# ── OUTILS — HONEYPOT ─────────────────────────────────────────────────────────

@mcp.tool()
def get_honeypot_attempts() -> list:
    """
    Retourne toutes les tentatives enregistrées par le honeypot /admin/.

    Chaque entrée contient : ip, user_agent, path, method, username, timestamp.
    """
    with _client() as c:
        return _check(
            c.get("/api/honeypot/", headers={"X-Honeypot-Key": HONEYPOT_API_KEY})
        )


# ── Entrée ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=MCP_PORT)
