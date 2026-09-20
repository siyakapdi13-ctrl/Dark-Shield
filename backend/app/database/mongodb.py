"""
MongoDB access layer.

The rest of the application talks to a small `Repository` interface so the
storage engine is swappable. Two implementations are provided:

* `MongoRepository`     – production, backed by MongoDB Atlas via Motor.
* `InMemoryRepository`  – development/demo fallback used automatically when
                          `MONGODB_URI` is empty or the connection fails.

Only the repository knows about collections, indexes and Mongo documents.
Services never import pymongo/motor directly.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from app.config import get_settings

logger = logging.getLogger(__name__)

COLLECTIONS = ("users", "analyses", "detections", "feedback", "chat_sessions", "analytics")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:24]


class Repository(Protocol):
    """Storage contract used by services."""

    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def ping(self) -> bool: ...

    # analyses
    async def insert_analysis(self, doc: Dict[str, Any]) -> str: ...
    async def get_analysis(self, analysis_id: str, user_id: str) -> Optional[Dict[str, Any]]: ...
    async def list_analyses(self, user_id: str, *, search: str = "", risk: str = "", sort: str = "createdAt", order: int = -1, page: int = 1, page_size: int = 10) -> Dict[str, Any]: ...
    async def delete_analysis(self, analysis_id: str, user_id: str) -> bool: ...
    async def all_analyses(self, user_id: str) -> List[Dict[str, Any]]: ...

    # users
    async def upsert_user(self, doc: Dict[str, Any]) -> None: ...

    # feedback
    async def insert_feedback(self, doc: Dict[str, Any]) -> str: ...
    async def feedback_summary(self, user_id: Optional[str] = None) -> Dict[str, int]: ...

    # chat
    async def append_chat(self, session_id: str, user_id: str, messages: List[Dict[str, Any]]) -> None: ...
    async def get_chat(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]: ...


# --------------------------------------------------------------------------- #
# In-memory implementation (demo / tests)
# --------------------------------------------------------------------------- #
class InMemoryRepository:
    def __init__(self) -> None:
        self.store: Dict[str, Dict[str, Dict[str, Any]]] = {c: {} for c in COLLECTIONS}

    async def connect(self) -> None:
        logger.warning("Using in-memory repository (no MONGODB_URI configured). Data will not persist.")

    async def close(self) -> None:
        return None

    async def ping(self) -> bool:
        return True

    # analyses ---------------------------------------------------------------
    async def insert_analysis(self, doc: Dict[str, Any]) -> str:
        _id = doc.get("_id") or _new_id()
        doc = {**doc, "_id": _id, "createdAt": doc.get("createdAt") or _now()}
        self.store["analyses"][_id] = doc
        for d in doc.get("detections", []):
            det_id = d.get("id") or _new_id()
            self.store["detections"][det_id] = {**d, "_id": det_id, "analysisId": _id, "userId": doc["userId"]}
        return _id

    async def get_analysis(self, analysis_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        doc = self.store["analyses"].get(analysis_id)
        if doc and doc.get("userId") == user_id:
            return dict(doc)
        return None

    async def all_analyses(self, user_id: str) -> List[Dict[str, Any]]:
        return [dict(d) for d in self.store["analyses"].values() if d.get("userId") == user_id]

    async def list_analyses(self, user_id, *, search="", risk="", sort="createdAt", order=-1, page=1, page_size=10):
        items = await self.all_analyses(user_id)
        if search:
            s = search.lower()
            items = [i for i in items if s in i.get("url", "").lower() or s in i.get("website", "").lower()]
        if risk and risk.lower() != "all":
            items = [i for i in items if i.get("riskLevel", "").lower() == risk.lower()]
        items.sort(key=lambda i: i.get(sort) or 0, reverse=(order == -1))
        total = len(items)
        start = (page - 1) * page_size
        return {"items": items[start : start + page_size], "total": total, "page": page, "pageSize": page_size}

    async def delete_analysis(self, analysis_id: str, user_id: str) -> bool:
        doc = self.store["analyses"].get(analysis_id)
        if not doc or doc.get("userId") != user_id:
            return False
        del self.store["analyses"][analysis_id]
        for k in [k for k, v in self.store["detections"].items() if v.get("analysisId") == analysis_id]:
            del self.store["detections"][k]
        return True

    # users ------------------------------------------------------------------
    async def upsert_user(self, doc: Dict[str, Any]) -> None:
        existing = self.store["users"].get(doc["_id"], {})
        self.store["users"][doc["_id"]] = {**existing, **doc, "updatedAt": _now(), "createdAt": existing.get("createdAt", _now())}

    # feedback ---------------------------------------------------------------
    async def insert_feedback(self, doc: Dict[str, Any]) -> str:
        _id = _new_id()
        self.store["feedback"][_id] = {**doc, "_id": _id, "createdAt": _now()}
        return _id

    async def feedback_summary(self, user_id: Optional[str] = None) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for f in self.store["feedback"].values():
            if user_id and f.get("userId") != user_id:
                continue
            summary[f["feedbackType"]] = summary.get(f["feedbackType"], 0) + 1
        return summary

    # chat -------------------------------------------------------------------
    async def append_chat(self, session_id: str, user_id: str, messages: List[Dict[str, Any]]) -> None:
        session = self.store["chat_sessions"].setdefault(session_id, {"_id": session_id, "userId": user_id, "messages": [], "createdAt": _now()})
        session["messages"].extend(messages)
        session["updatedAt"] = _now()

    async def get_chat(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        s = self.store["chat_sessions"].get(session_id)
        return dict(s) if s and s.get("userId") == user_id else None


# --------------------------------------------------------------------------- #
# MongoDB implementation (Motor)
# --------------------------------------------------------------------------- #
class MongoRepository:
    def __init__(self, uri: str, database: str) -> None:
        self._uri = uri
        self._db_name = database
        self._client = None
        self.db = None

    async def connect(self) -> None:
        from motor.motor_asyncio import AsyncIOMotorClient  # imported lazily

        self._client = AsyncIOMotorClient(self._uri, serverSelectionTimeoutMS=5000)
        self.db = self._client[self._db_name]
        await self._client.admin.command("ping")
        await self._ensure_indexes()
        logger.info("Connected to MongoDB database '%s'", self._db_name)

    async def _ensure_indexes(self) -> None:
        await self.db.analyses.create_index([("userId", 1), ("createdAt", -1)])
        await self.db.analyses.create_index([("userId", 1), ("url", 1)])
        await self.db.analyses.create_index([("riskLevel", 1)])
        await self.db.detections.create_index([("analysisId", 1)])
        await self.db.detections.create_index([("type", 1)])
        await self.db.feedback.create_index([("detectionId", 1)])
        await self.db.feedback.create_index([("userId", 1), ("createdAt", -1)])
        await self.db.chat_sessions.create_index([("userId", 1), ("updatedAt", -1)])
        await self.db.users.create_index([("email", 1)])

    async def close(self) -> None:
        if self._client:
            self._client.close()

    async def ping(self) -> bool:
        try:
            await self._client.admin.command("ping")
            return True
        except Exception:  # pragma: no cover
            return False

    # analyses ---------------------------------------------------------------
    async def insert_analysis(self, doc: Dict[str, Any]) -> str:
        _id = doc.get("_id") or _new_id()
        doc = {**doc, "_id": _id, "createdAt": doc.get("createdAt") or _now()}
        await self.db.analyses.insert_one(doc)
        if doc.get("detections"):
            await self.db.detections.insert_many(
                [{**d, "_id": d.get("id") or _new_id(), "analysisId": _id, "userId": doc["userId"]} for d in doc["detections"]]
            )
        return _id

    async def get_analysis(self, analysis_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.analyses.find_one({"_id": analysis_id, "userId": user_id})

    async def all_analyses(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.db.analyses.find({"userId": user_id}).to_list(length=5000)

    async def list_analyses(self, user_id, *, search="", risk="", sort="createdAt", order=-1, page=1, page_size=10):
        query: Dict[str, Any] = {"userId": user_id}
        if search:
            query["$or"] = [{"url": {"$regex": search, "$options": "i"}}, {"website": {"$regex": search, "$options": "i"}}]
        if risk and risk.lower() != "all":
            query["riskLevel"] = {"$regex": f"^{risk}$", "$options": "i"}
        total = await self.db.analyses.count_documents(query)
        cursor = self.db.analyses.find(query).sort(sort, order).skip((page - 1) * page_size).limit(page_size)
        return {"items": await cursor.to_list(length=page_size), "total": total, "page": page, "pageSize": page_size}

    async def delete_analysis(self, analysis_id: str, user_id: str) -> bool:
        res = await self.db.analyses.delete_one({"_id": analysis_id, "userId": user_id})
        if res.deleted_count:
            await self.db.detections.delete_many({"analysisId": analysis_id})
        return bool(res.deleted_count)

    # users ------------------------------------------------------------------
    async def upsert_user(self, doc: Dict[str, Any]) -> None:
        await self.db.users.update_one(
            {"_id": doc["_id"]},
            {"$set": {**doc, "updatedAt": _now()}, "$setOnInsert": {"createdAt": _now()}},
            upsert=True,
        )

    # feedback ---------------------------------------------------------------
    async def insert_feedback(self, doc: Dict[str, Any]) -> str:
        _id = _new_id()
        await self.db.feedback.insert_one({**doc, "_id": _id, "createdAt": _now()})
        return _id

    async def feedback_summary(self, user_id: Optional[str] = None) -> Dict[str, int]:
        match = {"userId": user_id} if user_id else {}
        pipeline = [{"$match": match}, {"$group": {"_id": "$feedbackType", "count": {"$sum": 1}}}]
        return {row["_id"]: row["count"] async for row in self.db.feedback.aggregate(pipeline)}

    # chat -------------------------------------------------------------------
    async def append_chat(self, session_id: str, user_id: str, messages: List[Dict[str, Any]]) -> None:
        await self.db.chat_sessions.update_one(
            {"_id": session_id, "userId": user_id},
            {"$push": {"messages": {"$each": messages}}, "$set": {"updatedAt": _now()}, "$setOnInsert": {"createdAt": _now()}},
            upsert=True,
        )

    async def get_chat(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.chat_sessions.find_one({"_id": session_id, "userId": user_id})


# --------------------------------------------------------------------------- #
# Factory / singleton
# --------------------------------------------------------------------------- #
_repository: Optional[Repository] = None


async def init_repository() -> Repository:
    global _repository
    settings = get_settings()
    if settings.mongodb_uri:
        repo: Repository = MongoRepository(settings.mongodb_uri, settings.mongodb_database)
        try:
            await repo.connect()
            _repository = repo
            return repo
        except Exception as exc:  # pragma: no cover - network dependent
            logger.error("MongoDB connection failed (%s). Falling back to in-memory storage.", exc)
    repo = InMemoryRepository()
    await repo.connect()
    _repository = repo
    return repo


def get_repository() -> Repository:
    if _repository is None:
        raise RuntimeError("Repository not initialised. Call init_repository() on startup.")
    return _repository


async def close_repository() -> None:
    if _repository is not None:
        await _repository.close()
