"""
FastAPI dependencies: authentication (Clerk), rate limiting, shared services.

Clerk issues RS256 JWTs. The backend validates them against Clerk's JWKS
endpoint (derived from the publishable/secret key configuration). Passwords are
never stored — Clerk owns credentials, we only keep the Clerk `user_id`.

In development with `AUTH_DEV_BYPASS=true` and no Clerk keys configured, a demo
user is injected so the full product can be explored locally.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, Header, HTTPException, Request, status

from app.config import Settings, get_settings
from app.database import get_cache, get_repository

logger = logging.getLogger(__name__)

DEMO_USER = {
    "id": "user_demo_dark_shield",
    "email": "demo@darkshield.app",
    "name": "Demo User",
    "avatar": "",
}


@dataclass
class CurrentUser:
    id: str
    email: str = ""
    name: str = ""
    avatar: str = ""
    claims: Optional[Dict[str, Any]] = None


class ClerkTokenVerifier:
    """Verifies Clerk-issued JWTs using the tenant JWKS (cached)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._jwks: Optional[Dict[str, Any]] = None
        self._jwks_fetched_at: float = 0.0

    def _jwks_url(self) -> Optional[str]:
        if self.settings.clerk_jwks_url:
            return self.settings.clerk_jwks_url
        if self.settings.clerk_issuer:
            return self.settings.clerk_issuer.rstrip("/") + "/.well-known/jwks.json"
        return None

    async def _get_jwks(self) -> Dict[str, Any]:
        if self._jwks and time.time() - self._jwks_fetched_at < 3600:
            return self._jwks
        url = self._jwks_url()
        if url:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                self._jwks = resp.json()
        elif self.settings.clerk_secret_key:
            # Backend API fallback: https://api.clerk.com/v1/jwks
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    "https://api.clerk.com/v1/jwks",
                    headers={"Authorization": f"Bearer {self.settings.clerk_secret_key}"},
                )
                resp.raise_for_status()
                self._jwks = resp.json()
        else:
            raise RuntimeError("Clerk is not configured (no CLERK_JWKS_URL / CLERK_ISSUER / CLERK_SECRET_KEY)")
        self._jwks_fetched_at = time.time()
        return self._jwks

    async def verify(self, token: str) -> Dict[str, Any]:
        from jose import jwt  # lazy import
        from jose.exceptions import JWTError

        jwks = await self._get_jwks()
        try:
            header = jwt.get_unverified_header(token)
            key = next((k for k in jwks.get("keys", []) if k.get("kid") == header.get("kid")), None)
            if key is None:
                raise JWTError("Signing key not found")
            claims = jwt.decode(
                token,
                key,
                algorithms=[header.get("alg", "RS256")],
                options={"verify_aud": False},
                issuer=self.settings.clerk_issuer or None,
            )
            return claims
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_TOKEN", "message": str(exc)})


_verifier: Optional[ClerkTokenVerifier] = None


def get_verifier(settings: Settings = Depends(get_settings)) -> ClerkTokenVerifier:
    global _verifier
    if _verifier is None:
        _verifier = ClerkTokenVerifier(settings)
    return _verifier


def _clerk_configured(settings: Settings) -> bool:
    return bool(settings.clerk_secret_key or settings.clerk_jwks_url or settings.clerk_issuer)


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    settings: Settings = Depends(get_settings),
    verifier: ClerkTokenVerifier = Depends(get_verifier),
) -> CurrentUser:
    """Resolve the authenticated Clerk user from the `Authorization: Bearer` header."""
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if token and _clerk_configured(settings):
        claims = await verifier.verify(token)
        user = CurrentUser(
            id=claims.get("sub", ""),
            email=claims.get("email", "") or claims.get("primary_email", ""),
            name=claims.get("name", "") or claims.get("full_name", ""),
            avatar=claims.get("image_url", "") or claims.get("picture", ""),
            claims=claims,
        )
    elif settings.auth_dev_bypass and not settings.is_production:
        user = CurrentUser(**DEMO_USER)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Authentication required."},
        )

    if not user.id:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Invalid identity."})

    # Keep a lightweight profile in MongoDB (no passwords — Clerk owns credentials).
    try:
        await get_repository().upsert_user({"_id": user.id, "email": user.email, "name": user.name, "avatar": user.avatar})
    except Exception as exc:  # pragma: no cover
        logger.debug("User upsert skipped: %s", exc)
    return user


async def rate_limit(request: Request, user: CurrentUser = Depends(get_current_user), settings: Settings = Depends(get_settings)) -> None:
    """Simple fixed-window rate limiter backed by Redis (or memory fallback)."""
    key = f"ratelimit:{user.id}:{int(time.time() // 60)}"
    count = await get_cache().incr_with_ttl(key, ttl=60)
    if count > settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "RATE_LIMITED", "message": "Too many requests. Please slow down."},
        )
