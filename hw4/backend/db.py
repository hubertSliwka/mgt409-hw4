"""Read campus_customs.db through a column map so the seed and Canvas packs both work.

Every query in the shop goes through here. The Canvas database may spell its columns
differently from the development seed (``price`` versus ``price_usd``, ``image_path``
versus ``image``), so the table and column names are resolved once from
``PRAGMA table_info`` and reused for the life of the process.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
import json
from typing import Any, Iterable, Iterator

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
DEFAULT_DB = PROJECT_DIR / "data" / "campus_customs.db"
PRODUCT_IMAGE_DIRS = ("data/products", "data/product_images", "products", "images")

# Candidate spellings, most specific first. The first name present in the file wins.
CATALOGUE_TABLES = ("catalogue", "catalog", "products", "product")
INVENTORY_TABLES = ("inventory", "stock", "inventory_levels", "product_inventory")
USER_TABLES = ("users", "user", "customers", "accounts")
CHAT_TABLES = ("chat_messages", "chat_history", "messages", "conversations")

CATALOGUE_COLUMNS = {
    "id": ("product_id", "id", "sku", "item_id"),
    "name": ("name", "title", "product_name", "item_name"),
    "price": ("price", "price_usd", "unit_price", "retail_price", "cost"),
    "description": ("description", "design_description", "product_description", "details", "long_description"),
    "image": ("image_file_path", "image_path", "image", "image_url", "image_file", "photo", "picture"),
    "category": ("garment_type", "category", "product_type", "type", "collection"),
    "color": ("colors", "primary_color", "color", "colour"),
    "tags": ("search_tags", "tags", "keywords"),
    "material": ("material", "fabric"),
}

INVENTORY_COLUMNS = {
    "product": ("product_id", "catalogue_id", "catalog_id", "item_id", "sku", "id"),
    "size": ("size", "size_name", "variant", "size_label"),
    "quantity": ("quantity", "qty", "stock", "stock_level", "on_hand", "units", "count", "available"),
}

USER_COLUMNS = {
    "id": ("user_id", "id", "customer_id"),
    "email": ("email", "email_address", "username"),
    "password": ("password_hash", "password", "hashed_password", "pwd_hash", "passwd"),
    "first_name": ("first_name", "firstname", "given_name", "fname"),
    "last_name": ("last_name", "lastname", "surname", "family_name", "lname"),
    "created_at": ("created_at", "created", "signup_date", "date_joined"),
}


# Packs spell the garment type freely ("short-sleeve T-shirt", "hooded pullover sweatshirt").
# These rules fold those into the handful of families the shop filters by.
FAMILY_RULES = (
    ("quarter-zip", "quarter-zip"),
    ("1/4 zip", "quarter-zip"),
    ("hood", "hoodie"),
    ("crew", "crewneck"),
    ("mockneck", "crewneck"),
    ("jacket", "jacket"),
    ("fleece", "jacket"),
    ("vest", "jacket"),
    ("t-shirt", "t-shirt"),
    ("tee", "t-shirt"),
    ("polo", "shirt"),
    ("shirt", "shirt"),
    ("sweatshirt", "crewneck"),
    ("sweater", "crewneck"),
    ("hat", "accessory"),
    ("cap", "accessory"),
    ("beanie", "accessory"),
)

FAMILY_FALLBACK = "apparel"


def family(*parts: str) -> str:
    """Fold a free-text garment type into one shopping category."""
    text = " ".join(part or "" for part in parts).lower()
    for needle, name in FAMILY_RULES:
        if needle in text:
            return name
    return FAMILY_FALLBACK


class SchemaError(RuntimeError):
    """The database exists but is missing a table or column the shop needs."""


@dataclass(frozen=True)
class TableMap:
    """One resolved table: its real name plus the real name of each column we use."""

    table: str
    columns: dict[str, str]

    def column(self, role: str) -> str:
        name = self.columns.get(role)
        if name is None:
            raise SchemaError(f"Table {self.table!r} has no column for {role!r}.")
        return name

    def has(self, role: str) -> bool:
        return role in self.columns


@dataclass(frozen=True)
class Schema:
    catalogue: TableMap
    inventory: TableMap | None
    users: TableMap | None
    chat_table: str
    chat_key: str
    required_user_columns: tuple[str, ...] = ()


def db_path() -> Path:
    return Path(os.getenv("CAMPUS_CUSTOMS_DB", str(DEFAULT_DB))).resolve()


def connect() -> sqlite3.Connection:
    path = db_path()
    if not path.exists():
        raise SystemExit(
            f"Database not found: {path}\n"
            "Place the Canvas data pack at data/campus_customs.db, or build the development "
            "copy with: python scripts/seed_dev_data.py --data-dir data"
        )
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    """Open a connection and always close it: SQLite holds a file lock while one is open."""
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()


def table_names(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')").fetchall()
    return [row["name"] for row in rows]


def pick_table(available: Iterable[str], candidates: Iterable[str]) -> str | None:
    lowered = {name.lower(): name for name in available}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    return None


def map_columns(connection: sqlite3.Connection, table: str, roles: dict[str, tuple[str, ...]]) -> TableMap:
    present = {row["name"].lower(): row["name"] for row in connection.execute(f'PRAGMA table_info("{table}")')}
    resolved: dict[str, str] = {}
    for role, candidates in roles.items():
        for candidate in candidates:
            if candidate in present:
                resolved[role] = present[candidate]
                break
    return TableMap(table=table, columns=resolved)


@lru_cache(maxsize=1)
def schema() -> Schema:
    """Resolve table and column names once; later calls reuse the cached map."""
    with session() as connection:
        names = table_names(connection)

        catalogue_table = pick_table(names, CATALOGUE_TABLES)
        if catalogue_table is None:
            raise SchemaError(f"No catalogue table in {db_path()}. Looked for {CATALOGUE_TABLES}.")
        catalogue = map_columns(connection, catalogue_table, CATALOGUE_COLUMNS)
        for required in ("id", "name", "price"):
            catalogue.column(required)

        inventory_table = pick_table(names, INVENTORY_TABLES)
        inventory = map_columns(connection, inventory_table, INVENTORY_COLUMNS) if inventory_table else None

        user_table = pick_table(names, USER_TABLES)
        users = map_columns(connection, user_table, USER_COLUMNS) if user_table else None

        chat_table = pick_table(names, CHAT_TABLES) or "chat_messages"
        chat_key = primary_key(connection, chat_table) or "rowid"
        required = required_columns(connection, user_table) if user_table else ()

    return Schema(
        catalogue=catalogue,
        inventory=inventory,
        users=users,
        chat_table=chat_table,
        chat_key=chat_key,
        required_user_columns=required,
    )


def primary_key(connection: sqlite3.Connection, table: str) -> str | None:
    """Order chat history by the table's own key: packs spell it id, message_id, ..."""
    for row in connection.execute(f'PRAGMA table_info("{table}")'):
        if row["pk"]:
            return row["name"]
    return None


def required_columns(connection: sqlite3.Connection, table: str) -> tuple[str, ...]:
    """NOT NULL columns with no default, which an INSERT has to fill itself."""
    return tuple(
        row["name"]
        for row in connection.execute(f'PRAGMA table_info("{table}")')
        if row["notnull"] and row["dflt_value"] is None and not row["pk"]
    )


def ensure_support_tables() -> None:
    """Create the tables this homework adds (users, chat history) when the pack lacks them."""
    with session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id       INTEGER PRIMARY KEY,
                first_name    TEXT NOT NULL,
                last_name     TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL
            );
            """
        )
        current = schema()
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS "{current.chat_table}" (
                message_id INTEGER PRIMARY KEY,
                user_id    INTEGER,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
    schema.cache_clear()


def image_filename(raw: object) -> str:
    """Catalogue rows store paths like data/products/x.jpg; the API serves the basename."""
    text = str(raw or "").replace("\\", "/").strip()
    return text.rsplit("/", 1)[-1]


def text_list(raw: object) -> list[str]:
    """Some packs store colours and tags as a JSON array in a TEXT column."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(item).strip() for item in raw if str(item).strip()]
    text = str(raw).strip()
    if text.startswith("["):
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            loaded = []
        if isinstance(loaded, list):
            return [str(item).strip() for item in loaded if str(item).strip()]
    return [part.strip() for part in text.split(",") if part.strip()]


def product_row(row: sqlite3.Row, table: TableMap) -> dict[str, Any]:
    keys = row.keys()

    def value(role: str) -> Any:
        name = table.columns.get(role)
        return row[name] if name in keys else None

    price = value("price")
    colors = text_list(value("color"))
    name = str(value("name") or "Campus Customs item")
    garment_type = str(value("category") or "").strip()
    return {
        "product_id": str(value("id")),
        "name": name,
        "price": round(float(price), 2) if price is not None else 0.0,
        "description": str(value("description") or "").strip(),
        "garment_type": garment_type,
        "category": family(garment_type, name),
        "color": ", ".join(colors),
        "colors": colors,
        "tags": text_list(value("tags")),
        "material": str(value("material") or ""),
        "image": image_filename(value("image")),
    }


def select_clause(table: TableMap, roles: Iterable[str]) -> str:
    parts = [f'"{table.table}"."{table.column(role)}" AS "{role}"' for role in roles if table.has(role)]
    return ", ".join(parts)


def all_products(limit: int | None = None) -> list[dict[str, Any]]:
    current = schema().catalogue
    roles = [role for role in CATALOGUE_COLUMNS if current.has(role)]
    query = f'SELECT {select_clause(current, roles)} FROM "{current.table}" ORDER BY "{current.column("name")}"'
    if limit:
        query += f" LIMIT {int(limit)}"
    with session() as connection:
        rows = connection.execute(query).fetchall()
    return [product_row(row, TableMap(current.table, {role: role for role in roles})) for row in rows]


def product_by_id(product_id: str) -> dict[str, Any] | None:
    current = schema().catalogue
    roles = [role for role in CATALOGUE_COLUMNS if current.has(role)]
    query = (
        f'SELECT {select_clause(current, roles)} FROM "{current.table}" '
        f'WHERE "{current.table}"."{current.column("id")}" = ?'
    )
    with session() as connection:
        row = connection.execute(query, (str(product_id),)).fetchone()
    if row is None:
        return None
    return product_row(row, TableMap(current.table, {role: role for role in roles}))


def stock_for(product_id: str) -> list[dict[str, Any]]:
    """Return per-size stock, or an empty list when the pack has no inventory table."""
    current = schema()
    inventory = current.inventory
    if inventory is None or not inventory.has("size") or not inventory.has("quantity"):
        return []
    query = (
        f'SELECT "{inventory.column("size")}" AS size, "{inventory.column("quantity")}" AS quantity '
        f'FROM "{inventory.table}" WHERE "{inventory.column("product")}" = ?'
    )
    with session() as connection:
        rows = connection.execute(query, (str(product_id),)).fetchall()
    order = {"XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4, "XXL": 5, "2XL": 5, "3XL": 6}
    sizes = [{"size": str(row["size"]), "quantity": int(row["quantity"] or 0)} for row in rows]
    return sorted(sizes, key=lambda item: order.get(item["size"].upper(), 99))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
