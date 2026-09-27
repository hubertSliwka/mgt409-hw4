import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api";
import { useAuth } from "../state/AuthContext";
import { usePageContext } from "../state/PageContext";
import type { ChatMessage, ProductCard } from "../types";
import { ProductTile } from "./ProductTile";

const GUEST_KEY = "campus_customs_guest_chat";
const SUGGESTIONS = [
  "what hoodies do you have?",
  "do you have this in M?",
  "show me something in navy",
];

type Bubble = ChatMessage & { products?: ProductCard[]; source?: "database" | "general" };

function loadGuestHistory(): Bubble[] {
  try {
    const raw = sessionStorage.getItem(GUEST_KEY);
    return raw ? (JSON.parse(raw) as Bubble[]) : [];
  } catch {
    return [];
  }
}

export function ChatWidget() {
  const { user } = useAuth();
  const { context, draft, setDraft, openSignal, setContext } = usePageContext();
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Bubble[]>(loadGuestHistory);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [unread, setUnread] = useState(false);
  const streamRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // A signed-in shopper picks up the conversation they left behind.
  useEffect(() => {
    if (!user) return;
    api
      .chatHistory()
      .then(({ history }) => setMessages(history.map((message) => ({ ...message }))))
      .catch(() => setError("Could not load your chat history."));
  }, [user]);

  useEffect(() => {
    if (!user) sessionStorage.setItem(GUEST_KEY, JSON.stringify(messages.slice(-20)));
  }, [messages, user]);

  useEffect(() => {
    if (openSignal === 0) return;
    setOpen(true);
    window.setTimeout(() => inputRef.current?.focus(), 120);
  }, [openSignal]);

  useEffect(() => {
    if (open) {
      setUnread(false);
      streamRef.current?.scrollTo({ top: streamRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [open, messages]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && open) setOpen(false);
      if (event.key === "/" && !open && document.activeElement?.tagName !== "INPUT") {
        event.preventDefault();
        setOpen(true);
        window.setTimeout(() => inputRef.current?.focus(), 120);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const send = useCallback(
    async (text: string) => {
      const message = text.trim();
      if (!message || sending) return;
      setError("");
      setSending(true);
      setMessages((current) => [...current, { role: "user", content: message }]);
      setDraft("");

      try {
        const guestHistory = user
          ? []
          : messages.map(({ role, content }) => ({ role, content }));
        const reply = await api.sendChat(message, context, guestHistory);
        setMessages((current) => [
          ...current,
          {
            role: "assistant",
            content: reply.reply,
            products: reply.products,
            source: reply.source,
          },
        ]);
        if (!open) setUnread(true);
      } catch (problem) {
        setError(problem instanceof Error ? problem.message : "The shop assistant is offline.");
      } finally {
        setSending(false);
      }
    },
    [context, messages, open, sending, setDraft, user],
  );

  const openProduct = (product: ProductCard) => {
    setContext({ page: "product", product_id: product.product_id, product_name: product.name });
    navigate(`/products/${product.product_id}`);
  };

  return (
    <>
      <button
        type="button"
        className={`chat-launcher${open ? " chat-launcher--hidden" : ""}`}
        onClick={() => setOpen(true)}
        aria-label="Open the Campus Customs shop chat"
      >
        <span className="chat-launcher__icon" aria-hidden="true">
          &#128172;
        </span>
        <span className="chat-launcher__label">Ask the shop</span>
        {unread && <span className="chat-launcher__dot" aria-hidden="true" />}
      </button>

      <section className={`chat-panel${open ? " chat-panel--open" : ""}`} aria-hidden={!open}>
        <header className="chat-panel__head">
          <div>
            <p className="chat-panel__title">Campus Customs help</p>
            <p className="chat-panel__sub">
              {user ? `Signed in as ${user.first_name}` : "Chatting as a guest"}
            </p>
          </div>
          <button type="button" onClick={() => setOpen(false)} aria-label="Close chat">
            &times;
          </button>
        </header>

        <div className="chat-stream" ref={streamRef}>
          {messages.length === 0 && (
            <div className="chat-empty">
              <p>Ask about sizes, stock, prices, or what we have in your colour.</p>
              <div className="chat-chips">
                {SUGGESTIONS.map((suggestion) => (
                  <button key={suggestion} type="button" onClick={() => send(suggestion)}>
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((bubble, index) => (
            <div key={`${bubble.role}-${index}`} className={`bubble bubble--${bubble.role}`}>
              <p>{bubble.content}</p>
              {bubble.source === "database" && <span className="bubble__tag">from our stock list</span>}
              {bubble.products && bubble.products.length > 0 && (
                <div className="chat-results" data-testid="chat-results">
                  {bubble.products.map((product) => (
                    <ProductTile
                      key={product.product_id}
                      product={product}
                      compact
                      onSelect={openProduct}
                    />
                  ))}
                </div>
              )}
            </div>
          ))}

          {sending && (
            <div className="bubble bubble--assistant bubble--typing">
              <span />
              <span />
              <span />
            </div>
          )}
        </div>

        {error && <p className="chat-error">{error}</p>}

        <form
          className="chat-form"
          onSubmit={(event) => {
            event.preventDefault();
            void send(draft);
          }}
        >
          <input
            ref={inputRef}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={
              context.product_id ? `Ask about ${context.product_name ?? "this item"}` : "Ask about our gear"
            }
            aria-label="Message the Campus Customs shop assistant"
            maxLength={500}
          />
          <button type="submit" disabled={sending || !draft.trim()}>
            Send
          </button>
        </form>
      </section>
    </>
  );
}
