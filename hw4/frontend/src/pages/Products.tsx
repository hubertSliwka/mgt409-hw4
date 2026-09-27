import { useEffect, useMemo, useState } from "react";
import * as api from "../api";
import { ProductTile, TileSkeleton } from "../components/ProductTile";
import { usePageContext } from "../state/PageContext";
import type { ProductCard } from "../types";

type Sort = "featured" | "price-low" | "price-high" | "name";

const SORTS: { value: Sort; label: string }[] = [
  { value: "featured", label: "Featured" },
  { value: "price-low", label: "Price: low to high" },
  { value: "price-high", label: "Price: high to low" },
  { value: "name", label: "A to Z" },
];

export function Products() {
  const [products, setProducts] = useState<ProductCard[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [category, setCategory] = useState("");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<Sort>("featured");
  const [loading, setLoading] = useState(true);
  const [inStockOnly, setInStockOnly] = useState(false);
  const { setContext, openChat } = usePageContext();

  useEffect(() => {
    setContext({ page: "products", product_id: null });
  }, [setContext]);

  // Debounced so typing does not fire a request per keystroke.
  useEffect(() => {
    setLoading(true);
    const timer = window.setTimeout(() => {
      api
        .listProducts(query, category)
        .then((data) => {
          setProducts(data.products);
          if (data.categories.length) setCategories(data.categories);
        })
        .finally(() => setLoading(false));
    }, 220);
    return () => window.clearTimeout(timer);
  }, [query, category]);

  const shown = useMemo(() => {
    const list = inStockOnly ? products.filter((item) => item.in_stock) : [...products];
    switch (sort) {
      case "price-low":
        return list.sort((a, b) => a.price - b.price);
      case "price-high":
        return list.sort((a, b) => b.price - a.price);
      case "name":
        return list.sort((a, b) => a.name.localeCompare(b.name));
      default:
        return list;
    }
  }, [products, sort, inStockOnly]);

  return (
    <div className="page">
      <section className="page__head">
        <div>
          <p className="eyebrow">The racks</p>
          <h1>Everything we have printed lately</h1>
        </div>
        <button type="button" className="button button--ghost" onClick={() => openChat("")}>
          Ask the shop assistant
        </button>
      </section>

      <div className="filters">
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search hoodies, crewnecks, navy, fencing&hellip;"
          aria-label="Search the catalogue"
        />
        <div className="chips" role="group" aria-label="Filter by category">
          <button
            type="button"
            className={category === "" ? "chip chip--on" : "chip"}
            onClick={() => setCategory("")}
          >
            All
          </button>
          {categories.map((name) => (
            <button
              key={name}
              type="button"
              className={category === name ? "chip chip--on" : "chip"}
              onClick={() => setCategory(name)}
            >
              {name}
            </button>
          ))}
        </div>
        <label className="toggle">
          <input
            type="checkbox"
            checked={inStockOnly}
            onChange={(event) => setInStockOnly(event.target.checked)}
          />
          In stock only
        </label>
        <label className="select">
          Sort
          <select value={sort} onChange={(event) => setSort(event.target.value as Sort)}>
            {SORTS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <p className="count">{loading ? "Looking…" : `${shown.length} items`}</p>

      <div className="grid">
        {loading
          ? Array.from({ length: 8 }, (_, index) => <TileSkeleton key={index} />)
          : shown.map((product) => <ProductTile key={product.product_id} product={product} />)}
      </div>

      {!loading && shown.length === 0 && (
        <div className="empty">
          <p>Nothing matched that. Try a colour, a sport, or ask the shop assistant.</p>
          <button type="button" className="button button--solid" onClick={() => openChat(query)}>
            Ask about &ldquo;{query || "our gear"}&rdquo;
          </button>
        </div>
      )}
    </div>
  );
}
