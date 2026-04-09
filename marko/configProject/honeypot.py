"""
Honeypot pour l'URL /admin/.

Affiche une fausse page de login Django identique à la vraie.
Toute tentative d'accès (GET ou POST) est loggée et sauvegardée en base avec :
  - IP source
  - User-Agent
  - Identifiants soumis (si POST)
  - Date/heure

En cas de POST, renvoie toujours "identifiants incorrects" pour maintenir
les bots engagés et enregistrer plusieurs tentatives.
"""

import logging

from django.http import HttpResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger("honeypot")

_FAKE_LOGIN_PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Connexion | Administration Django</title>
<style>
  html * {{ box-sizing: border-box; }}
  body {{ background: #f8f9fa; margin: 0; padding: 0;
         font-family: "Roboto","Lucida Grande","DejaVu Sans","Bitstream Vera Sans",
         Verdana,Arial,sans-serif; font-size: 14px; color: #333; }}
  #header {{ background: #417690; color: #fff; padding: 10px 40px; }}
  #header h1 {{ font-size: 18px; margin: 0; font-weight: 300; }}
  #container {{ max-width: 400px; margin: 80px auto; }}
  #content-main {{ background: #fff; padding: 30px 40px;
                   border: 1px solid #ddd; border-radius: 4px; }}
  h2 {{ font-size: 16px; margin: 0 0 20px; text-align: center; }}
  .form-row {{ margin-bottom: 16px; }}
  label {{ display: block; font-weight: bold; margin-bottom: 4px; }}
  input[type=text], input[type=password] {{
    width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 3px;
    font-size: 14px; }}
  .submit-row {{ margin-top: 20px; }}
  input[type=submit] {{
    background: #417690; color: #fff; border: none; padding: 10px 20px;
    width: 100%; font-size: 15px; cursor: pointer; border-radius: 3px; }}
  input[type=submit]:hover {{ background: #205067; }}
  .errornote {{ background: #ffc; border: 1px solid #ccc; border-radius: 3px;
                padding: 10px; margin-bottom: 16px; font-size: 13px; color: #c00; }}
</style>
</head>
<body>
<div id="header"><h1>Administration Django</h1></div>
<div id="container">
  <div id="content-main">
    <h2>Connexion</h2>
    {error}
    <form method="post" action="/admin/login/?next=/admin/">
      <input type="hidden" name="csrfmiddlewaretoken" value="fake-csrf-token">
      <div class="form-row">
        <label for="id_username">Nom d'utilisateur :</label>
        <input type="text" name="username" id="id_username" autofocus required>
      </div>
      <div class="form-row">
        <label for="id_password">Mot de passe :</label>
        <input type="password" name="password" id="id_password" required>
      </div>
      <div class="submit-row">
        <input type="submit" value="Connexion">
      </div>
    </form>
  </div>
</div>
</body>
</html>"""


def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _save_attempt(ip, user_agent, path, method, username=""):
    try:
        from api.models import HoneypotAttempt
        HoneypotAttempt.objects.create(
            ip=ip,
            user_agent=user_agent,
            path=path,
            method=method,
            username=username,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Impossible de sauvegarder la tentative honeypot en DB : %s", exc)


@csrf_exempt
def honeypot_admin(request):
    """Vue honeypot montée sur /admin/ et ses sous-chemins."""
    ip = _get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "unknown")
    path = request.path
    timestamp = now().isoformat()

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        logger.warning(
            "HONEYPOT POST | ip=%s | ua=%s | path=%s | user=%r | pass=%r | ts=%s",
            ip, user_agent, path, username, password, timestamp,
        )
        _save_attempt(ip, user_agent, path, "POST", username)
        error_html = (
            '<p class="errornote">Saisissez des identifiants valides. '
            'Notez que les champs peuvent être sensibles à la casse.</p>'
        )
        return HttpResponse(
            _FAKE_LOGIN_PAGE.format(error=error_html),
            status=200,
            content_type="text/html",
        )

    logger.warning(
        "HONEYPOT GET  | ip=%s | ua=%s | path=%s | ts=%s",
        ip, user_agent, path, timestamp,
    )
    _save_attempt(ip, user_agent, path, "GET")
    return HttpResponse(
        _FAKE_LOGIN_PAGE.format(error=""),
        status=200,
        content_type="text/html",
    )
