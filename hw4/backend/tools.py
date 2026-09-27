"""Give the Campus Customs agent database-backed lookups and write the audit trail.

Every price, size and quantity the agent says out loud comes from one of these
functions, which read campus_customs.db through ``db.py``. Nothing here invents a
number, and each call appends one record to ``output/audit_trail.json``.
"""

from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path
from typing import Any, Iterable

import db
from models import AuditRecord, ProductCard, ProductDetail, SearchResult, SizeStock, StockReport

AUDIT_TRAIL_PATH = db.PROJECT_DIR / "output" / "audit_trail.json"

# Result caps keep one answer small enough to render and cheap enough to send to the model.
MAX_CARDS = 8
MAX_AUDIT_FIELD = 220
CATALOGUE_TTL_SECONDS = 60

# Shopper words on the left, catalogue words on the right.
CATEGORY_SYNONYMS = {
    "hoodie": ("hoodie", "hood", "hooded", "pullover"),
    "hoodies": ("hoodie", "hood", "hooded", "pullover"),
    "sweatshirt": ("sweatshirt", "crewneck", "hooded"),
    "sweatshirts": ("sweatshirt", "crewneck", "hooded"),
    "crewneck": ("crewneck", "sweatshirt"),
    "crewnecks": ("crewneck", "sweatshirt"),
    "tee": ("t-shirt", "tee", "shirt"),
    "tees": ("t-shirt", "tee", "shirt"),
    "tshirt": ("t-shirt", "tee", "shirt"),
    "tshirts": ("t-shirt", "tee", "shirt"),
    "shirt": ("t-shirt", "shirt"),
    "shirts": ("t-shirt", "shirt"),
    "quarterzip": ("quarter-zip", "zip"),
    "zip": ("quarter-zip", "zip", "full-zip"),
    "jacket": ("jacket", "fleece"),
    "jackets": ("jacket", "fleece"),
    "fleece": ("fleece", "jacket"),
    "sweater": ("sweater", "crewneck"),
    "hat": ("hat", "cap", "beanie"),
    "cap": ("hat", "cap"),
}

STOPWORDS = frozenset(
    "a an and any are do does for got have how i in is it me my of on or our show some the "
    "there this to we what which you your got want like need looking".split()
)

_audit_lock = threading.Lock()
_catalogue_cache: tuple[float, list[dict[str, Any]]] | None = None


def tokens(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9-]+", (text or "").lower()) if word not in STOPWORDS]


def truncate(value: object, limit: int = MAX_AUDIT_FIELD) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def record_audit(
    *,
    run_id: str,
    tool: str,
    args: object = "",
    result: object = "",
    stop_reason: str = "ok",
    duration_ms: int = 0,
    path: Path = AUDIT_TRAIL_PATH,
) -> None:
    """Append one agent-loop step. The file is never rewritten, only extended."""
    record = AuditRecord(
        time=db.utc_now(),
        run_id=run_id,
        tool=tool,
        args=truncate(args),
        result=truncate(result),
        stop_reason=stop_reason,  # type: ignore[arg-type]
        duration_ms=duration_ms,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with _audit_lock:
        existing: list[dict[str, Any]] = []
        if path.exists():
            raw = path.read_text(encoding="utf-8").strip()
            if raw:
                try:
                    loaded = json.loads(raw)
                except json.JSONDecodeError as error:
                    raise RuntimeError(f"Existing audit trail is not valid JSON: {path}") from error
                if not isinstance(loaded, list):
                    raise RuntimeError(f"Existing audit trail must be a JSON array: {path}")
                existing = loaded
        existing.append(record.model_dump())
        path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")


def catalogue_snapshot(force: bool = False) -> list[dict[str, Any]]:
    """Cache the catalogue briefly: a chat turn can score it several times per question."""
    global _catalogue_cache
    now = time.monotonic()
    if not force and _catalogue_cache and now - _catalogue_cache[0] < CATALOGUE_TTL_SECONDS:
        return _catalogue_cache[1]
    products = db.all_products()
    _catalogue_cache = (now, products)
    return products


def clear_catalogue_cache() -> None:
    global _catalogue_cache
    _catalogue_cache = None


def expand(words: Iterable[str]) -> set[str]:
    expanded: set[str] = set()
    for word in words:
        expanded.add(word)
        expanded.update(CATEGORY_SYNONYMS.get(word, ()))
    return expanded


def score_product(query_words: set[str], product: dict[str, Any]) -> float:
    """Weight a name hit above a category hit above a description hit."""
    if not query_words:
        return 0.0
    name_words = set(tokens(product["name"]))
    category_words = expand(tokens(f"{product.get('category','')}"))
    colour_words = set(tokens(product.get("color", "")))
    description_words = set(tokens(product.get("description", "")))

    score = 0.0
    score += 3.0 * len(query_words & name_words)
    score += 2.0 * len(query_words & category_words)
    score += 1.5 * len(query_words & colour_words)
    score += 0.5 * len(query_words & description_words)

    joined = product["name"].lower()
    for word in query_words:
        if len(word) > 3 and word in joined:
            score += 1.0
    return score


def to_card(product: dict[str, Any], in_stock: bool = True) -> ProductCard:
    blurb = product.get("description", "")
    if len(blurb) > 150:
        blurb = blurb[:147].rstrip() + "…"
    return ProductCard(
        product_id=product["product_id"],
        name=product["name"],
        price=product["price"],
        image=product.get("image", ""),
        category=product.get("category", "apparel"),
        blurb=blurb,
        in_stock=in_stock,
    )


def has_stock(product_id: int) -> bool:
    sizes = db.stock_for(product_id)
    return any(size["quantity"] > 0 for size in sizes) if sizes else True


def best_match(query: str) -> dict[str, Any] | None:
    query_words = expand(tokens(query))
    ranked = [(score_product(query_words, product), product) for product in catalogue_snapshot()]
    ranked = [pair for pair in ranked if pair[0] > 0]
    if not ranked:
        return None
    ranked.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
    return ranked[0][1]


def resolve_product(query: str | None, product_id: int | None) -> dict[str, Any] | None:
    if product_id:
        found = db.product_by_id(int(product_id))
        if found:
            return found
    if query:
        return best_match(query)
    return None


def rank_products(query: str, limit: int) -> tuple[list[ProductCard], int]:
    """Score every product against a phrase. Used by the agent tool and by the site search."""
    query_words = expand(tokens(query))
    ranked = [(score_product(query_words, product), product) for product in catalogue_snapshot()]
    ranked = [pair for pair in ranked if pair[0] > 0]
    ranked.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    cards = [to_card(product, has_stock(product["product_id"])) for _, product in ranked[:limit]]
    return cards, len(ranked)


def search_catalogue(query: str, limit: int = MAX_CARDS, *, run_id: str = "-") -> SearchResult:
    """Rank the catalogue by a shopper's phrase and return at most `limit` cards."""
    started = time.monotonic()
    limit = max(1, min(int(limit), MAX_CARDS))
    matches, total = rank_products(query, limit)
    result = SearchResult(query=query, matches=matches, total_found=total)
    record_audit(
        run_id=run_id,
        tool="search_catalogue",
        args={"query": query, "limit": limit},
        result={"total_found": result.total_found, "returned": len(matches)},
        stop_reason="empty" if not matches else ("capped" if result.total_found > limit else "ok"),
        duration_ms=int((time.monotonic() - started) * 1000),
    )
    return result


def product_detail(query: str | None = None, product_id: int | None = None, *, run_id: str = "-") -> ProductDetail:
    """Description, price and colour for one product, looked up by name or by id."""
    started = time.monotonic()
    product = resolve_product(query, product_id)
    if product is None:
        record_audit(
            run_id=run_id,
            tool="product_detail",
            args={"query": query, "product_id": product_id},
            result="no catalogue match",
            stop_reason="not_found",
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return ProductDetail(product_id=0, name=str(query or ""), price=0.0, found=False)

    detail = ProductDetail(
        product_id=product["product_id"],
        name=product["name"],
        price=product["price"],
        description=product.get("description", ""),
        category=product.get("category", "apparel"),
        color=product.get("color", ""),
        material=product.get("material", ""),
        image=product.get("image", ""),
        found=True,
    )
    record_audit(
        run_id=run_id,
        tool="product_detail",
        args={"query": query, "product_id": product_id},
        result={"product_id": detail.product_id, "price": detail.price},
        duration_ms=int((time.monotonic() - started) * 1000),
    )
    return detail


def stock_report(
    query: str | None = None,
    size: str | None = None,
    product_id: int | None = None,
    *,
    run_id: str = "-",
) -> StockReport:
    """Per-size quantities for one product; `size` narrows the answer to that size."""
    started = time.monotonic()
    product = resolve_product(query, product_id)
    if product is None:
        record_audit(
            run_id=run_id,
            tool="stock_report",
            args={"query": query, "size": size, "product_id": product_id},
            result="no catalogue match",
            stop_reason="not_found",
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return StockReport(product_id=0, name=str(query or ""), price=0.0, found=False, checked_size=size)

    rows = db.stock_for(product["product_id"])
    wanted = (size or "").strip().upper()
    if wanted:
        rows = [row for row in rows if row["size"].upper() == wanted] or rows

    sizes = [SizeStock(size=row["size"], quantity=row["quantity"], available=row["quantity"] > 0) for row in rows]
    report = StockReport(
        product_id=product["product_id"],
        name=product["name"],
        price=product["price"],
        sizes=sizes,
        total_units=sum(item.quantity for item in sizes),
        checked_size=wanted or None,
        found=True,
    )
    record_audit(
        run_id=run_id,
        tool="stock_report",
        args={"query": query, "size": size, "product_id": product_id},
        result={"product_id": report.product_id, "total_units": report.total_units, "sizes": len(sizes)},
        stop_reason="empty" if not sizes else "ok",
        duration_ms=int((time.monotonic() - started) * 1000),
    )
    return report
