"""Consistent API envelope helpers."""
from __future__ import annotations

from typing import Any, Optional

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


def success(data: Any = None, message: str = "OK", status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=jsonable_encoder({"success": True, "data": data, "message": message}))


def error(code: str, message: str, status_code: int = 400, details: Optional[Any] = None) -> JSONResponse:
    payload: dict = {"success": False, "error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))
