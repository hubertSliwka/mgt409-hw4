import type {
  AccountUser,
  ChatMessage,
  ChatResponse,
  PageContext,
  ProductCard,
  ProductDetail,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "";
const TOKEN_KEY = "campus_customs_token";

export function readToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function writeToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function imageUrl(file: string): string {
  return file ? `${BASE}/api/images/${file}` : "";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = readToken();
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* the server did not send JSON; keep the status message */
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export function listProducts(query = "", category = ""): Promise<{
  products: ProductCard[];
  categories: string[];
  total: number;
}> {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  if (category) params.set("category", category);
  const suffix = params.toString() ? `?${params}` : "";
  return request(`/api/products${suffix}`);
}

export function getProduct(productId: string): Promise<ProductDetail> {
  return request(`/api/products/${encodeURIComponent(productId)}`);
}

export function signup(payload: {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}): Promise<{ token: string; user: AccountUser }> {
  return request("/api/auth/signup", { method: "POST", body: JSON.stringify(payload) });
}

export function login(email: string, password: string): Promise<{ token: string; user: AccountUser }> {
  return request("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function me(): Promise<AccountUser> {
  return request("/api/auth/me");
}

export function chatHistory(): Promise<{ history: ChatMessage[] }> {
  return request("/api/chat/history");
}

export function sendChat(
  message: string,
  pageContext: PageContext,
  guestHistory: ChatMessage[],
): Promise<ChatResponse> {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      page_context: pageContext,
      guest_history: guestHistory.slice(-12),
    }),
  });
}
