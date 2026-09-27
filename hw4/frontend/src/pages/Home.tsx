import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "../api";
import { ProductTile, TileSkeleton } from "../components/ProductTile";
import { usePageContext } from "../state/PageContext";
import type { ProductCard } from "../types";

const PROMISES = [
  {
    title: "Printed a block from campus",
    body: "Every run is pressed in our New Haven shop, so a club order placed on Monday is on backs by the weekend.",
  },
  {
    title: "Licensed, not knock-off",
    body: "Residential college crests, varsity marks and class years are all run under the university licence.",
  },
  {
    title: "Ask before you buy",
    body: "Our shop assistant reads the same stock list the register does, so the size it quotes is the size on the shelf.",
  },
];

export function Home() {
  const [featured, setFeatured] = useState<ProductCard[]>([]);
  const [loading, setLoading] = useState(true);
  const { setContext, openChat } = usePageContext();

  useEffect(() => {
    setContext({ page: "home", product_id: null });
    api
      .listProducts()
      .then(({ products }) => setFeatured(products.filter((item) => item.in_stock).slice(0, 6)))
      .finally(() => setLoading(false));
  }, [setContext]);

  return (
    <div className="page">
      <section className="hero">
        <div className="hero__copy">
          <p className="eyebrow">New Haven &middot; since the last Game we won</p>
          <h1>
            Yale blue, <span>cut for the walk</span> to your 9am.
          </h1>
          <p className="lede">
            Campus Customs prints hoodies, crewnecks and tees for students, parents, alumni and every
            residential college that thinks it is the best one. Pick a piece, or ask our shop assistant
            what is actually in your size.
          </p>
          <div className="hero__actions">
            <Link className="button button--solid button--lg" to="/products">
              Shop the racks
            </Link>
            <button
              type="button"
              className="button button--ghost button--lg"
              onClick={() => openChat("what hoodies do you have?")}
            >
              Ask about hoodies
            </button>
          </div>
        </div>
        <div className="hero__art" aria-hidden="true">
          <span className="hero__blob" />
          <span className="hero__blob hero__blob--two" />
          <p className="hero__stamp">
            CAMPUS
            <br />
            CUSTOMS
          </p>
        </div>
      </section>

      <section className="strip">
        {PROMISES.map((promise) => (
          <article key={promise.title}>
            <h2>{promise.title}</h2>
            <p>{promise.body}</p>
          </article>
        ))}
      </section>

      <section className="section">
        <div className="section__head">
          <h2>On the front table</h2>
          <Link to="/products">See everything &rarr;</Link>
        </div>
        <div className="grid">
          {loading
            ? Array.from({ length: 6 }, (_, index) => <TileSkeleton key={index} />)
            : featured.map((product) => <ProductTile key={product.product_id} product={product} />)}
        </div>
      </section>
    </div>
  );
}
