"""Typed objects shared by the FastAPI routes, the PydanticAI agent and its tools.

The agent's structured output is what the website renders, so every field here exists
because some part of the page or the audit trail needs it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class ProductCard(BaseModel):
    """One product tile. Same shape whether the page or the chat produced it."""

    product_id: str = Field(description="Catalogue id, used by the front end to open the detail page.")
    name: str
    price: float = Field(ge=0, description="Price in USD, copied from the catalogue row.")
    image: str = Field(default="", description="Image file name served from /api/images/.")
    category: str = Field(default="apparel")
    blurb: str = Field(default="", description="One-line description short enough for a card.")
    in_stock: bool = Field(default=True, description="False when every size is at zero.")


class SizeStock(BaseModel):
    """Stock for one size, straight from the inventory table."""

    size: str
    quantity: int = Field(ge=0)
    available: bool = Field(description="quantity > 0, so the agent never has to do the comparison.")


class StockReport(BaseModel):
    """What the stock tool returns: enough to answer 'do you have this in M?' honestly."""

    product_id: str
    name: str
    price: float = Field(ge=0)
    sizes: list[SizeStock] = Field(default_factory=list)
    total_units: int = Field(ge=0, default=0)
    checked_size: str | None = Field(default=None, description="Size the shopper asked about, if any.")
    found: bool = Field(default=True, description="False when no catalogue row matched the request.")


class ProductDetail(BaseModel):
    """Full product record for description and price questions."""

    product_id: str
    name: str
    price: float = Field(ge=0)
    description: str = ""
    category: str = "apparel"
    color: str = ""
    material: str = ""
    image: str = ""
    found: bool = True


class SearchResult(BaseModel):
    """Catalogue search result: the cards the website draws plus what was searched for."""

    query: str
    matches: list[ProductCard] = Field(default_factory=list)
    total_found: int = Field(ge=0, default=0)


class ShopReply(BaseModel):
    """The agent's structured answer. `products` is the API contract that updates the page."""

    reply: str = Field(description="Message shown in the chat bubble. Plain text, no markdown tables.")
    products: list[ProductCard] = Field(
        default_factory=list,
        description="Cards to render on the site. Empty when the question was not about specific items.",
    )
    highlight_product_id: str | None = Field(
        default=None, description="Product the shopper is asking about, so the page can open it."
    )
    source: Literal["database", "general"] = Field(
        default="general",
        description="database when any price, stock or description came from a tool call.",
    )


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: str = ""


class PageContext(BaseModel):
    """What the shopper is looking at, so 'do you have this in pink?' resolves."""

    page: str = Field(default="home", description="Route name: home, products, product, about, login, signup.")
    product_id: str | None = Field(default=None, description="Catalogue id when a detail page is open.")
    product_name: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    page_context: PageContext = Field(default_factory=PageContext)
    guest_history: list[ChatMessage] = Field(
        default_factory=list, description="Turns held by the browser for shoppers who are not logged in."
    )


class ChatResponse(ShopReply):
    """Reply plus the history the front end should show after this turn."""

    history: list[ChatMessage] = Field(default_factory=list)


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AccountUser(BaseModel):
    """Everything the site and the agent may see about a shopper. No password material."""

    user_id: int
    first_name: str
    last_name: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: AccountUser


class AuditRecord(BaseModel):
    """One appended line of output/audit_trail.json."""

    time: str
    run_id: str
    tool: str
    args: str = Field(default="", description="Short argument summary, truncated for the log.")
    result: str = Field(default="", description="Short result summary, truncated for the log.")
    stop_reason: Literal["ok", "not_found", "empty", "capped", "error", "refused"] = "ok"
    duration_ms: int = Field(ge=0, default=0)
