export type ProductCard = {
  product_id: number;
  name: string;
  price: number;
  image: string;
  category: string;
  blurb: string;
  in_stock: boolean;
};

export type SizeStock = {
  size: string;
  quantity: number;
};

export type ProductDetail = {
  product_id: number;
  name: string;
  price: number;
  description: string;
  category: string;
  color: string;
  material: string;
  image: string;
  sizes: SizeStock[];
  in_stock: boolean;
};

export type AccountUser = {
  user_id: number;
  first_name: string;
  last_name: string;
  email: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  created_at?: string;
};

export type PageContext = {
  page: string;
  product_id?: number | null;
  product_name?: string | null;
};

export type ChatResponse = {
  reply: string;
  products: ProductCard[];
  highlight_product_id: number | null;
  source: "database" | "general";
  history: ChatMessage[];
};
