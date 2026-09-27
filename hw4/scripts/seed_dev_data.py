"""Build a local data/campus_customs.db (and placeholder product images) for development.

The graded run uses the Canvas data pack. This script only exists so the site, the
agent and the checks can run on a machine that does not have that pack yet; drop the
real ``data/campus_customs.db`` in place and the backend reads that instead.

    python scripts/seed_dev_data.py --data-dir data
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import bcrypt
from PIL import Image, ImageDraw, ImageFont

# Ordered smallest to largest: the site and the agent report stock in this order.
SIZES = ("XS", "S", "M", "L", "XL", "XXL")

# (substring of the catalogue product_type, canonical category, base price in USD)
CATEGORY_RULES = (
    ("quarter-zip", "quarter-zip", 78.0),
    ("hood", "hoodie", 64.0),
    ("crewneck", "crewneck", 58.0),
    ("jacket", "jacket", 95.0),
    ("fleece", "jacket", 95.0),
    ("t-shirt", "t-shirt", 28.0),
    ("shirt", "t-shirt", 30.0),
    ("sweatshirt", "crewneck", 58.0),
    ("sweater", "crewneck", 62.0),
)

FALLBACK_CATEGORY = ("apparel", 45.0)

TEST_USER = ("Test", "Bulldog", "test@campuscustoms.yale.edu", "password")

YALE_BLUE = (0, 53, 107)

COLOR_SWATCHES = (
    ("navy", (12, 35, 64)),
    ("royal blue", (0, 71, 171)),
    ("light blue", (137, 176, 222)),
    ("heather gray", (150, 152, 154)),
    ("charcoal", (54, 58, 61)),
    ("gray", (128, 128, 128)),
    ("grey", (128, 128, 128)),
    ("black", (28, 28, 28)),
    ("white", (238, 238, 235)),
    ("maroon", (110, 31, 45)),
    ("red", (155, 34, 38)),
    ("green", (32, 82, 56)),
    ("cream", (233, 223, 200)),
    ("tan", (203, 178, 140)),
    ("pink", (214, 149, 168)),
    ("purple", (88, 62, 123)),
    ("yellow", (222, 184, 68)),
    ("orange", (201, 105, 44)),
    ("blue", (0, 53, 107)),
)

FONT_CANDIDATES = ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf")


def stable_int(key: str, modulo: int) -> int:
    """Hash to a fixed value so re-seeding reproduces the same prices and stock."""
    return int(sha256(key.encode("utf-8")).hexdigest(), 16) % modulo


def categorise(product_type: str) -> tuple[str, float]:
    lowered = (product_type or "").lower()
    for needle, category, base_price in CATEGORY_RULES:
        if needle in lowered:
            return category, base_price
    return FALLBACK_CATEGORY


def price_for(entry: dict[str, object]) -> float:
    category, base = categorise(str(entry.get("product_type", "")))
    bump = stable_int(f"{entry.get('image_path', '')}{category}", 5) * 3.0
    return round(base + bump - 0.01, 2)


def swatch(color: str | None) -> tuple[int, int, int]:
    lowered = (color or "").lower().strip()
    for name, rgb in COLOR_SWATCHES:
        if name in lowered:
            return rgb
    return YALE_BLUE


def load_font(size: int):
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, face, width: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in text.split():
        probe = f"{line} {word}".strip()
        if draw.textlength(probe, font=face) <= width:
            line = probe
            continue
        if line:
            lines.append(line)
        line = word
    if line:
        lines.append(line)
    return lines[:3]


def draw_placeholder(path: Path, title: str, color: str, category: str) -> None:
    """Stand in for a Canvas product photo so the storefront renders during development."""
    canvas = Image.new("RGB", (900, 900), (247, 246, 243))
    draw = ImageDraw.Draw(canvas)
    garment = swatch(color)

    draw.rounded_rectangle((150, 170, 750, 690), radius=48, fill=garment)
    if category in {"hoodie", "quarter-zip"}:
        draw.rounded_rectangle((330, 140, 570, 300), radius=90, fill=garment)
        draw.rounded_rectangle((372, 176, 528, 268), radius=70, fill=(247, 246, 243))
    draw.rounded_rectangle((60, 210, 200, 470), radius=44, fill=garment)
    draw.rounded_rectangle((700, 210, 840, 470), radius=44, fill=garment)

    ink = (247, 246, 243) if sum(garment) < 460 else (18, 32, 55)
    draw.text((450, 402), "CAMPUS", font=load_font(58), fill=ink, anchor="mm")
    draw.text((450, 468), "CUSTOMS", font=load_font(58), fill=ink, anchor="mm")

    caption = load_font(30)
    for index, line in enumerate(wrap(draw, title, caption, 780)):
        draw.text((450, 752 + index * 38), line, font=caption, fill=(38, 44, 56), anchor="mm")

    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, quality=88)


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS catalogue (
            product_id    INTEGER PRIMARY KEY,
            name          TEXT NOT NULL,
            category      TEXT NOT NULL,
            product_type  TEXT,
            primary_color TEXT,
            description   TEXT,
            price         REAL NOT NULL,
            image_path    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS inventory (
            inventory_id INTEGER PRIMARY KEY,
            product_id   INTEGER NOT NULL REFERENCES catalogue(product_id),
            size         TEXT NOT NULL,
            quantity     INTEGER NOT NULL,
            UNIQUE (product_id, size)
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY,
            first_name    TEXT NOT NULL,
            last_name     TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id INTEGER PRIMARY KEY,
            user_id    INTEGER REFERENCES users(user_id),
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id, message_id);
        """
    )


def seed_catalogue(connection: sqlite3.Connection, entries: list[dict[str, object]], data_dir: Path) -> int:
    rows = 0
    for entry in entries:
        image_path = str(entry.get("image_path") or "")
        if not image_path:
            continue
        title = str(entry.get("title") or "").strip()
        # The photo title is often more specific than product_type, so read both.
        category, _ = categorise(f"{entry.get('product_type', '')} {title}")
        blocked = entry.get("analysis_status") == "provider_blocked"
        if not title or blocked:
            title = f"Campus Customs {category}"
        # A blocked photo has a refusal notice where its description should be, not copy.
        description = "" if blocked else str(entry.get("design_description") or "").strip()
        features = None if blocked else entry.get("features")
        if isinstance(features, list) and features:
            description = f"{description} Features: {', '.join(str(item) for item in features)}."
        connection.execute(
            "INSERT INTO catalogue (name, category, product_type, primary_color, description, price, image_path)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                title,
                category,
                str(entry.get("product_type") or category),
                str(entry.get("primary_color") or ""),
                description.strip() or "Campus Customs original, printed in New Haven.",
                price_for(entry),
                image_path,
            ),
        )
        rows += 1

        target = data_dir / "products" / Path(image_path).name
        if not target.exists():
            draw_placeholder(target, title, str(entry.get("primary_color") or ""), category)
    return rows


def seed_inventory(connection: sqlite3.Connection) -> int:
    rows = 0
    for product_id, name in connection.execute("SELECT product_id, name FROM catalogue").fetchall():
        for size in SIZES:
            quantity = stable_int(f"{name}|{size}", 19)
            # Leave predictable empty sizes so the agent has something honest to refuse.
            if size in {"XS", "XXL"} and stable_int(name, 3) == 0:
                quantity = 0
            connection.execute(
                "INSERT OR REPLACE INTO inventory (product_id, size, quantity) VALUES (?, ?, ?)",
                (product_id, size, quantity),
            )
            rows += 1
    return rows


def seed_users(connection: sqlite3.Connection) -> None:
    first_name, last_name, email, password = TEST_USER
    digest = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    connection.execute(
        "INSERT OR IGNORE INTO users (first_name, last_name, email, password_hash, created_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (first_name, last_name, email, digest, datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Folder holding campus_customs.db and products/.")
    parser.add_argument("--catalogue", type=Path, default=None, help="Seed catalogue JSON, default <data-dir>/catalogue_seed.json.")
    parser.add_argument("--force", action="store_true", help="Rebuild even when campus_customs.db already exists.")
    args = parser.parse_args()

    data_dir: Path = args.data_dir
    db_path = data_dir / "campus_customs.db"
    if db_path.exists() and not args.force:
        raise SystemExit(f"{db_path} already exists. Pass --force to rebuild it.")

    catalogue_path = args.catalogue or data_dir / "catalogue_seed.json"
    if not catalogue_path.exists():
        raise SystemExit(f"Seed catalogue not found: {catalogue_path}")

    entries = json.loads(catalogue_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError(f"Seed catalogue must be a JSON array: {catalogue_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    with sqlite3.connect(db_path) as connection:
        create_schema(connection)
        products = seed_catalogue(connection, entries, data_dir)
        stock_rows = seed_inventory(connection)
        seed_users(connection)
        connection.commit()

    print(f"wrote {db_path}: {products} products, {stock_rows} inventory rows, 1 test user")


if __name__ == "__main__":
    main()
