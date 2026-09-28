import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as api from "../api";
import { usePageContext } from "../state/PageContext";
import type { ProductDetail } from "../types";

const LOW_STOCK = 3;

export function ProductPage() {
  const { productId } = useParams();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [size, setSize] = useState<string>("");
  const [error, setError] = useState("");
  const { setContext, openChat } = usePageContext();

  useEffect(() => {
    if (!productId) return;
    setProduct(null);
    setSize("");
    api
      .getProduct(productId)
      .then((detail) => {
        setProduct(detail);
        setContext({ page: "product", product_id: detail.product_id, product_name: detail.name });
        const firstAvailable = detail.sizes.find((entry) => entry.quantity > 0);
        if (firstAvailable) setSize(firstAvailable.size);
      })
      .catch((problem: Error) => setError(problem.message));
  }, [productId, setContext]);

  const selected = useMemo(
    () => product?.sizes.find((entry) => entry.size === size) ?? null,
    [product, size],
  );

  if (error) {
    return (
      <div className="page">
        <p className="empty">{error}</p>
        <Link className="button button--ghost" to="/products">
          Back to the racks
        </Link>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="page detail detail--loading">
        <div className="detail__frame shimmer" />
        <div className="detail__body">
          <div className="shimmer line line--short" />
          <div className="shimmer line" />
          <div className="shimmer line" />
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <nav className="crumbs">
        <Link to="/products">Products</Link>
        <span aria-hidden="true">/</span>
        <span>{product.name}</span>
      </nav>

      <div className="detail">
        <div className="detail__frame">
          <img src={api.imageUrl(product.image)} alt={product.name} />
        </div>

        <div className="detail__body">
          <p className="eyebrow">{product.garment_type || product.category}</p>
          <h1>{product.name}</h1>
          <p className="detail__price">${product.price.toFixed(2)}</p>
          <p className="detail__text">{product.description}</p>

          <dl className="detail__facts">
            {product.color && (
              <div>
                <dt>Colour</dt>
                <dd>{product.color}</dd>
              </div>
            )}
            {product.material && (
              <div>
                <dt>Material</dt>
                <dd>{product.material}</dd>
              </div>
            )}
            <div>
              <dt>Item code</dt>
              <dd className="code">{product.product_id}</dd>
            </div>
          </dl>

          {product.sizes.length > 0 && (
            <div className="sizes">
              <p className="sizes__label">Size</p>
              <div className="sizes__row" role="group" aria-label="Choose a size">
                {product.sizes.map((entry) => (
                  <button
                    key={entry.size}
                    type="button"
                    className={`size${entry.size === size ? " size--on" : ""}`}
                    disabled={entry.quantity === 0}
                    title={entry.quantity === 0 ? "Out of stock" : `${entry.quantity} in stock`}
                    onClick={() => setSize(entry.size)}
                  >
                    {entry.size}
                  </button>
                ))}
              </div>
              <p className="sizes__note">
                {selected === null
                  ? "Pick a size to see what is on the shelf."
                  : selected.quantity === 0
                    ? `${selected.size} is out of stock right now.`
                    : selected.quantity <= LOW_STOCK
                      ? `Only ${selected.quantity} left in ${selected.size}.`
                      : `${selected.quantity} in stock in ${selected.size}.`}
              </p>
            </div>
          )}

          <div className="detail__actions">
            <button type="button" className="button button--solid button--lg" disabled={!product.in_stock}>
              {product.in_stock ? "Add to bag" : "Sold out"}
            </button>
            <button
              type="button"
              className="button button--ghost button--lg"
              onClick={() => openChat(size ? `do you have this in ${size}?` : "is this in stock?")}
            >
              Ask about this item
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
