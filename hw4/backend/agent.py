"""Wire the Campus Customs PydanticAI agent: model, prompt file, tools and deps.

``main.py`` imports :func:`answer` for the website's chat route. Running this file
directly is the quick way to test one message from a terminal.

    python agent.py --message "what hoodies do you have?"
    python agent.py --message "do you have this in M?" --product-id 3 --email test@campuscustoms.yale.edu
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

import db
import tools
from models import AccountUser, ChatMessage, PageContext, ProductCard, ShopReply

# The PydanticAI startup banner is noise in a web server log.
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "prompt.md"
DEFAULT_MODEL = "gpt-4o-mini"
MAX_HISTORY_TURNS = 12
MAX_CARDS_IN_REPLY = 6

REFUSAL = (
    "I can't help with that one, but I'm good on Campus Customs gear: sizes, stock, prices "
    "and what we have in your colour. What are you shopping for?"
)
OUTAGE = "Sorry, the shop assistant is having trouble right now. Please try again in a moment."

load_dotenv(db.PROJECT_DIR / ".env")
load_dotenv(db.PROJECT_DIR.parent / ".env")


@dataclass
class ShopDeps:
    """Everything the agent is allowed to know about who is chatting and where."""

    run_id: str
    customer: AccountUser | None = None
    page: PageContext = field(default_factory=PageContext)


def provider_settings() -> dict[str, object]:
    """Use Portkey when configured, falling back to a plain OpenAI key."""
    portkey_key = os.getenv("PORTKEY_API_KEY")
    if portkey_key:
        return {
            "api_key": portkey_key,
            "base_url": "https://api.portkey.ai/v1",
            "default_headers": {"x-portkey-api-key": portkey_key, "x-portkey-provider": "openai"},
        }
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return {"api_key": openai_key}
    raise SystemExit("Set PORTKEY_API_KEY or OPENAI_API_KEY in hw4/.env before starting the backend.")


def system_prompt() -> str:
    if not PROMPT_PATH.exists():
        raise SystemExit(f"System prompt missing: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_agent(model_name: str | None = None) -> Agent[ShopDeps, ShopReply]:
    client = AsyncOpenAI(**provider_settings())
    model = OpenAIChatModel(
        model_name or os.getenv("AGENT_MODEL", DEFAULT_MODEL),
        provider=OpenAIProvider(openai_client=client),
    )
    shop_agent = Agent(
        model,
        deps_type=ShopDeps,
        output_type=ShopReply,
        instructions=system_prompt(),
        retries=2,
    )

    @shop_agent.instructions
    def who_and_where(ctx: RunContext[ShopDeps]) -> str:
        """Append the live customer and page context to every run's instructions."""
        customer = ctx.deps.customer
        if customer is None:
            lines = ["Shopper: a guest who is not signed in. Do not use a name."]
        else:
            lines = [
                f"Shopper: {customer.first_name} {customer.last_name}, signed in as {customer.email}.",
                "Their past messages in this shop are included above as earlier turns.",
            ]
        page = ctx.deps.page
        if page.product_id:
            lines.append(
                f"Open page: the detail page for product_id {page.product_id} "
                f"({page.product_name or 'unnamed'}). 'This' and 'it' mean that product."
            )
        else:
            lines.append(f"Open page: {page.page}. No single product is on screen.")
        return "\n".join(lines)

    @shop_agent.tool
    def search_products(ctx: RunContext[ShopDeps], query: str, limit: int = MAX_CARDS_IN_REPLY) -> dict:
        """Search the catalogue for a kind of item and return matching products as cards."""
        return tools.search_catalogue(query, limit=limit, run_id=ctx.deps.run_id).model_dump()

    @shop_agent.tool
    def get_product_details(ctx: RunContext[ShopDeps], query: str = "", product_id: int | None = None) -> dict:
        """Look up one product's description, price, colour and material."""
        return tools.product_detail(
            query or None,
            product_id or ctx.deps.page.product_id,
            run_id=ctx.deps.run_id,
        ).model_dump()

    @shop_agent.tool
    def check_stock(
        ctx: RunContext[ShopDeps], query: str = "", size: str = "", product_id: int | None = None
    ) -> dict:
        """Check how many units of a product are in stock, by size when a size is given."""
        return tools.stock_report(
            query or None,
            size or None,
            product_id or ctx.deps.page.product_id,
            run_id=ctx.deps.run_id,
        ).model_dump()

    return shop_agent


_agent: Agent[ShopDeps, ShopReply] | None = None


def get_agent() -> Agent[ShopDeps, ShopReply]:
    """Build the agent once per process: the prompt file and HTTP client are reused."""
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def reload_agent() -> None:
    global _agent
    _agent = None


def to_model_messages(history: list[ChatMessage]) -> list[ModelMessage]:
    """Replay stored turns as PydanticAI messages so the agent remembers the shopper."""
    messages: list[ModelMessage] = []
    for turn in history[-MAX_HISTORY_TURNS:]:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


def is_content_filter(error: Exception) -> bool:
    """The provider blocks some messages outright; that is a refusal, not an outage."""
    text = str(error).lower()
    return "content_filter" in text or "response was filtered" in text or "content management policy" in text


def verify_cards(cards: list[ProductCard]) -> list[ProductCard]:
    """Re-read every card from the database so a wrong price cannot reach the page."""
    verified: list[ProductCard] = []
    seen: set[int] = set()
    for card in cards[:MAX_CARDS_IN_REPLY]:
        product = db.product_by_id(card.product_id)
        if product is None or card.product_id in seen:
            continue
        seen.add(card.product_id)
        verified.append(tools.to_card(product, tools.has_stock(product["product_id"])))
    return verified


async def answer(
    message: str,
    *,
    customer: AccountUser | None = None,
    page: PageContext | None = None,
    history: list[ChatMessage] | None = None,
) -> ShopReply:
    """Run one chat turn and return a reply whose product cards match the database."""
    run_id = uuid4().hex[:12]
    deps = ShopDeps(run_id=run_id, customer=customer, page=page or PageContext())
    started = time.monotonic()

    try:
        result = await get_agent().run(
            message,
            deps=deps,
            message_history=to_model_messages(history or []),
        )
    except Exception as error:  # noqa: BLE001 - one bad turn must not take the site down
        filtered = is_content_filter(error)
        tools.record_audit(
            run_id=run_id,
            tool="agent.run",
            args={"message": message, "page": deps.page.page},
            result=f"{type(error).__name__}: {error}",
            stop_reason="refused" if filtered else "error",
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return ShopReply(reply=REFUSAL if filtered else OUTAGE, products=[], source="general")

    reply = result.output
    reply.products = verify_cards(reply.products)
    if reply.products and reply.highlight_product_id is None and len(reply.products) == 1:
        reply.highlight_product_id = reply.products[0].product_id

    usage = result.usage
    tools.record_audit(
        run_id=run_id,
        tool="agent.run",
        args={"message": message, "page": deps.page.page, "product_id": deps.page.product_id},
        result={
            "cards": len(reply.products),
            "source": reply.source,
            "request_tokens": getattr(usage, "input_tokens", 0),
            "response_tokens": getattr(usage, "output_tokens", 0),
        },
        stop_reason="ok",
        duration_ms=int((time.monotonic() - started) * 1000),
    )
    return reply


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--message", required=True, help="Message to send to the shop agent.")
    parser.add_argument("--product-id", type=int, default=None, help="Product page the shopper is on.")
    parser.add_argument("--email", default=None, help="Sign the test message in as this account email.")
    parser.add_argument("--model", default=None, help="Override AGENT_MODEL for this run.")
    args = parser.parse_args()

    if args.model:
        os.environ["AGENT_MODEL"] = args.model

    customer: AccountUser | None = None
    if args.email:
        import main as api  # imported lazily: the CLI path does not need FastAPI otherwise

        customer = api.user_by_email(args.email)
        if customer is None:
            raise SystemExit(f"No account found for {args.email}")

    page = PageContext(page="product" if args.product_id else "home", product_id=args.product_id)
    reply = asyncio.run(answer(args.message, customer=customer, page=page))

    print(reply.reply)
    for card in reply.products:
        print(f"  [{card.product_id}] {card.name} — ${card.price:.2f} ({'in stock' if card.in_stock else 'sold out'})")
    print(f"source={reply.source} highlight={reply.highlight_product_id}")


if __name__ == "__main__":
    main()
