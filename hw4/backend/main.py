"""Serve the Campus Customs API: products, images, accounts and the agent chat route.

Run it from this folder:

    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import agent
import db
import security
import tools
from models import (
    AccountUser,
    AuthResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    LoginRequest,
    ProductCard,
    SignupRequest,
)

ALLOWED_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
)

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".gif")
MAX_HISTORY_MESSAGES = 40

# Several supplied photos are pillarboxed with black bars. They are trimmed once and cached.
IMAGE_CACHE = db.PROJECT_DIR / "data" / ".image_cache"
TRIMMABLE_SUFFIXES = (".jpg", ".jpeg", ".png")
BLACK_LEVEL = 26

app = FastAPI(title="Campus Customs API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    db.ensure_support_tables()
    tools.clear_catalogue_cache()


def user_from_row(row: sqlite3.Row | dict[str, Any], table) -> AccountUser:
    def value(role: str, default: str = "") -> str:
        column = table.columns.get(role)
        return str(row[column]) if column and row[column] is not None else default

    return AccountUser(
        user_id=int(value("id", "0") or 0),
        first_name=value("first_name", "Shopper"),
        last_name=value("last_name", ""),
        email=value("email"),
    )


def user_by_email(email: str) -> AccountUser | None:
    table = db.schema().users
    if table is None:
        return None
    query = f'SELECT * FROM "{table.table}" WHERE lower("{table.column("email")}") = ?'
    with db.session() as connection:
        row = connection.execute(query, (email.strip().lower(),)).fetchone()
    return user_from_row(row, table) if row else None


def user_by_id(user_id: int) -> AccountUser | None:
    table = db.schema().users
    if table is None:
        return None
    query = f'SELECT * FROM "{table.table}" WHERE "{table.column("id")}" = ?'
    with db.session() as connection:
        row = connection.execute(query, (user_id,)).fetchone()
    return user_from_row(row, table) if row else None


def current_user(request: Request) -> AccountUser | None:
    """Resolve the bearer token the front end stores after login. Guests get None."""
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    user_id = security.read_token(header.split(" ", 1)[1].strip())
    return user_by_id(user_id) if user_id else None


def require_user(request: Request) -> AccountUser:
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    return user


def save_message(user_id: int, role: str, content: str) -> None:
    table = db.schema().chat_table
    with db.session() as connection:
        connection.execute(
            f'INSERT INTO "{table}" (user_id, role, content, created_at) VALUES (?, ?, ?, ?)',
            (user_id, role, content, db.utc_now()),
        )
        connection.commit()


def load_history(user_id: int, limit: int = MAX_HISTORY_MESSAGES) -> list[ChatMessage]:
    current = db.schema()
    table, key = current.chat_table, current.chat_key
    with db.session() as connection:
        rows = connection.execute(
            f'SELECT role, content, created_at FROM "{table}" WHERE user_id = ?'
            f' ORDER BY "{key}" DESC LIMIT ?',
            (user_id, limit),
        ).fetchall()
    return [
        ChatMessage(role=row["role"], content=row["content"], created_at=str(row["created_at"] or ""))
        for row in reversed(rows)
    ]


@app.get("/api/health")
def health() -> dict[str, Any]:
    current = db.schema()
    return {
        "status": "ok",
        "database": str(db.db_path()),
        "catalogue_table": current.catalogue.table,
        "inventory_table": current.inventory.table if current.inventory else None,
        "products": len(tools.catalogue_snapshot()),
    }


@app.get("/api/products")
def list_products(
    q: str = Query(default="", max_length=120),
    category: str = Query(default="", max_length=60),
    limit: int = Query(default=120, ge=1, le=500),
) -> dict[str, Any]:
    if q:
        # The grid is not capped like the agent's tool: the shopper can scroll.
        cards, _ = tools.rank_products(q, limit)
    else:
        products = tools.catalogue_snapshot()
        cards = [tools.to_card(item, tools.has_stock(item["product_id"])) for item in products[:limit]]
    if category:
        cards = [card for card in cards if card.category.lower() == category.lower()]
    categories = sorted({item["category"] for item in tools.catalogue_snapshot() if item["category"]})
    return {"products": [card.model_dump() for card in cards], "categories": categories, "total": len(cards)}


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict[str, Any]:
    product = db.product_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    sizes = db.stock_for(product_id)
    return {
        **product,
        "sizes": sizes,
        "in_stock": any(size["quantity"] > 0 for size in sizes) if sizes else True,
    }


def content_box(rgb) -> tuple[int, int, int, int] | None:
    """Find the picture inside a letterboxed photo by dropping near-black rows and columns.

    Averaging a whole row or column first is what makes this survive the stray bright pixel
    that a plain bounding box trips over.
    """
    width, height = rgb.size
    gray = rgb.convert("L")
    columns = list(gray.resize((width, 1)).getdata())
    rows = list(gray.resize((1, height)).getdata())

    def span(profile: list[int]) -> tuple[int, int] | None:
        lit = [index for index, level in enumerate(profile) if level > BLACK_LEVEL]
        return (lit[0], lit[-1] + 1) if lit else None

    horizontal = span(columns)
    vertical = span(rows)
    if horizontal is None or vertical is None:
        return None
    return horizontal[0], vertical[0], horizontal[1], vertical[1]


def trimmed(source: Path) -> Path:
    """Return a copy with the black letterbox bars removed, building it once on first request."""
    if source.suffix.lower() not in TRIMMABLE_SUFFIXES:
        return source
    cached = IMAGE_CACHE / f"{source.stem}-{int(source.stat().st_mtime)}{source.suffix}"
    if cached.exists():
        return cached
    try:
        from PIL import Image

        with Image.open(source) as image:
            rgb = image.convert("RGB")
            box = content_box(rgb)
            if box is None:
                return source
            left, top, right, bottom = box
            if (right - left) >= rgb.width * 0.99 and (bottom - top) >= rgb.height * 0.99:
                return source
            # A dark garment on a dark backdrop can fool the scan; never crop away the product.
            if (right - left) * (bottom - top) < rgb.width * rgb.height * 0.45:
                return source
            IMAGE_CACHE.mkdir(parents=True, exist_ok=True)
            rgb.crop(box).save(cached, quality=90)
        return cached
    except Exception:  # noqa: BLE001 - a photo we cannot trim is still worth serving
        return source


@app.get("/api/images/{filename}")
def get_image(filename: str) -> FileResponse:
    safe = Path(filename).name
    if Path(safe).suffix.lower() not in IMAGE_SUFFIXES:
        raise HTTPException(status_code=404, detail="Not an image.")
    for folder in db.PRODUCT_IMAGE_DIRS:
        candidate = db.PROJECT_DIR / folder / safe
        if candidate.exists():
            return FileResponse(trimmed(candidate), headers={"Cache-Control": "public, max-age=86400"})
    raise HTTPException(status_code=404, detail="Image not found.")


@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(payload: SignupRequest) -> AuthResponse:
    table = db.schema().users
    if table is None:
        raise HTTPException(status_code=500, detail="This database has no users table.")
    if user_by_email(payload.email):
        raise HTTPException(status_code=409, detail="That email already has an account.")

    digest = security.hash_password(payload.password)
    values: dict[str, Any] = {
        table.column("first_name"): payload.first_name,
        table.column("last_name"): payload.last_name,
        table.column("email"): str(payload.email).lower(),
        table.column("password"): digest,
    }
    if table.has("created_at"):
        values[table.column("created_at")] = db.utc_now()
    # A pack may have its own NOT NULL columns, such as a single `name`. Fill them sensibly.
    for column in db.schema().required_user_columns:
        values.setdefault(column, f"{payload.first_name} {payload.last_name}".strip())

    columns = ", ".join(f'"{name}"' for name in values)
    placeholders = ", ".join("?" for _ in values)
    with db.session() as connection:
        cursor = connection.execute(
            f'INSERT INTO "{table.table}" ({columns}) VALUES ({placeholders})',
            tuple(values.values()),
        )
        connection.commit()
        user_id = int(cursor.lastrowid)

    user = user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=500, detail="Account was created but could not be read back.")
    return AuthResponse(token=security.issue_token(user.user_id), user=user)


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    table = db.schema().users
    if table is None:
        raise HTTPException(status_code=500, detail="This database has no users table.")
    query = f'SELECT * FROM "{table.table}" WHERE lower("{table.column("email")}") = ?'
    with db.session() as connection:
        row = connection.execute(query, (str(payload.email).strip().lower(),)).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        stored = str(row[table.column("password")] or "")
        if not security.verify_password(payload.password, stored):
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        user = user_from_row(row, table)
        # A pack that shipped a weak digest gets upgraded on the first successful login.
        if security.needs_rehash(stored):
            connection.execute(
                f'UPDATE "{table.table}" SET "{table.column("password")}" = ?'
                f' WHERE "{table.column("id")}" = ?',
                (security.hash_password(payload.password), user.user_id),
            )
            connection.commit()

    return AuthResponse(token=security.issue_token(user.user_id), user=user)


@app.get("/api/auth/me", response_model=AccountUser)
def me(user: AccountUser = Depends(require_user)) -> AccountUser:
    return user


@app.get("/api/chat/history")
def chat_history(request: Request) -> dict[str, Any]:
    user = current_user(request)
    if user is None:
        return {"history": []}
    return {"history": [message.model_dump() for message in load_history(user.user_id)]}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    user = current_user(request)
    history = load_history(user.user_id) if user else payload.guest_history[-12:]

    reply = await agent.answer(
        payload.message,
        customer=user,
        page=payload.page_context,
        history=history,
    )

    if user:
        save_message(user.user_id, "user", payload.message)
        save_message(user.user_id, "assistant", reply.reply)
        history = load_history(user.user_id)
    else:
        history = [
            *history,
            ChatMessage(role="user", content=payload.message, created_at=db.utc_now()),
            ChatMessage(role="assistant", content=reply.reply, created_at=db.utc_now()),
        ]

    return ChatResponse(
        reply=reply.reply,
        products=reply.products,
        highlight_product_id=reply.highlight_product_id,
        source=reply.source,
        history=history,
    )


@app.post("/api/chat/clear")
def clear_history(user: AccountUser = Depends(require_user)) -> dict[str, str]:
    table = db.schema().chat_table
    with db.session() as connection:
        connection.execute(f'DELETE FROM "{table}" WHERE user_id = ?', (user.user_id,))
        connection.commit()
    return {"status": "cleared"}


__all__ = ["app", "user_by_email", "user_by_id", "ProductCard"]
