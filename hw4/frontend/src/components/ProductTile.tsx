import { Link } from "react-router-dom";
import { imageUrl } from "../api";
import type { ProductCard } from "../types";

type TileProps = {
  product: ProductCard;
  compact?: boolean;
  /** When given, the tile is a button (used inside the chat panel) instead of a link. */
  onSelect?: (product: ProductCard) => void;
};

function TileInner({ product, compact }: { product: ProductCard; compact: boolean }) {
  return (
    <>
      <div className="tile__frame">
        <img src={imageUrl(product.image)} alt={product.name} loading="lazy" />
        {!product.in_stock && <span className="tile__flag">Sold out</span>}
      </div>
      <div className="tile__body">
        <p className="tile__eyebrow">{product.category}</p>
        <h3 className="tile__name">{product.name}</h3>
        {!compact && <p className="tile__blurb">{product.blurb}</p>}
        <p className="tile__price">${product.price.toFixed(2)}</p>
      </div>
    </>
  );
}

export function ProductTile({ product, compact = false, onSelect }: TileProps) {
  const className = compact ? "tile tile--compact" : "tile";

  if (onSelect) {
    return (
      <button
        type="button"
        className={className}
        onClick={() => onSelect(product)}
        data-testid={`product-tile-${product.product_id}`}
      >
        <TileInner product={product} compact={compact} />
      </button>
    );
  }

  return (
    <Link
      to={`/products/${product.product_id}`}
      className={className}
      data-testid={`product-tile-${product.product_id}`}
    >
      <TileInner product={product} compact={compact} />
    </Link>
  );
}

export function TileSkeleton() {
  return (
    <div className="tile tile--skeleton" aria-hidden="true">
      <div className="tile__frame shimmer" />
      <div className="tile__body">
        <div className="shimmer line line--short" />
        <div className="shimmer line" />
        <div className="shimmer line line--tiny" />
      </div>
    </div>
  );
}
