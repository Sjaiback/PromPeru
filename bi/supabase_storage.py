"""Cliente mínimo para respaldos privados en Supabase Storage."""

import hashlib
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings


class StorageConfigurationError(RuntimeError):
    pass


class StorageRequestError(RuntimeError):
    pass


def _configuration():
    base_url = settings.SUPABASE_URL.rstrip("/")
    secret = settings.SUPABASE_SERVICE_ROLE_KEY.strip()
    bucket = settings.SUPABASE_BACKUP_BUCKET.strip()
    if not base_url or not secret or not bucket:
        raise StorageConfigurationError(
            "Falta configurar SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY o "
            "SUPABASE_BACKUP_BUCKET en el servidor."
        )
    return base_url, secret, bucket


def _request(method, url, secret, payload=None, content_type=None):
    headers = {"apikey": secret}
    # Legacy service_role keys are JWTs and use Bearer authentication. New
    # sb_secret_* keys authenticate through the apikey header itself.
    if not secret.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {secret}"
    if content_type:
        headers["Content-Type"] = content_type
    request = Request(url, data=payload, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise StorageRequestError(
            f"Supabase Storage respondió {exc.code}: {detail[:300]}"
        ) from exc
    except URLError as exc:
        raise StorageRequestError(
            f"No fue posible conectar con Supabase Storage: {exc}"
        ) from exc


def _ensure_private_bucket(base_url, secret, bucket):
    payload = json.dumps(
        {"id": bucket, "name": bucket, "public": False}
    ).encode("utf-8")
    try:
        _request(
            "POST",
            f"{base_url}/storage/v1/bucket",
            secret,
            payload,
            "application/json",
        )
    except StorageRequestError as exc:
        detalle = str(exc).lower()
        if "409" not in detalle and "already exists" not in detalle:
            raise
        # If it already exists, enforce that it remains private.
        _request(
            "PUT",
            f"{base_url}/storage/v1/bucket/{quote(bucket)}",
            secret,
            payload,
            "application/json",
        )


def subir_respaldo(contenido, ruta):
    base_url, secret, bucket = _configuration()
    _ensure_private_bucket(base_url, secret, bucket)
    url = (
        f"{base_url}/storage/v1/object/{quote(bucket)}/"
        f"{quote(ruta, safe='/')}"
    )
    _request(
        "POST",
        url,
        secret,
        contenido,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    return {
        "bucket": bucket,
        "ruta": ruta,
        "tamano": len(contenido),
        "checksum": hashlib.sha256(contenido).hexdigest(),
    }


def descargar_respaldo(bucket, ruta):
    base_url, secret, _ = _configuration()
    url = (
        f"{base_url}/storage/v1/object/authenticated/{quote(bucket)}/"
        f"{quote(ruta, safe='/')}"
    )
    return _request("GET", url, secret)
