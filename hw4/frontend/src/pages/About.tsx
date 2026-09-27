import { useEffect } from "react";
import { Link } from "react-router-dom";
import { usePageContext } from "../state/PageContext";

const NUMBERS = [
  { value: "14", label: "residential colleges printed" },
  { value: "30+", label: "varsity and club teams outfitted" },
  { value: "48h", label: "typical turnaround on a club run" },
];

export function About() {
  const { setContext } = usePageContext();

  useEffect(() => {
    setContext({ page: "about", product_id: null });
  }, [setContext]);

  return (
    <div className="page">
      <section className="page__head">
        <div>
          <p className="eyebrow">About us</p>
          <h1>A print shop that happens to sell sweatshirts</h1>
        </div>
      </section>

      <div className="prose">
        <p>
          Campus Customs has been pressing Yale blue onto cotton in New Haven for long enough that we
          can tell which residential college someone is in by the crest they ask for. We started with
          team orders and intramural jerseys, and the storefront grew out of people asking whether
          they could just buy the hoodie off the sample rack.
        </p>
        <p>
          Everything we sell is licensed. The crests, the varsity marks, the class years and the
          residential college seals are printed under the university licence, which matters when you
          are buying a gift for a parent who will frame it. The rest is the part we care about most:
          heavyweight fleece that keeps its shape, prints that survive the laundry room in the
          basement, and a fit that works on a 9am walk across Cross Campus in February.
        </p>
        <p>
          We keep a real count of what is on the shelf. That is why the chat window in the corner can
          tell you that a medium is gone instead of promising one and disappointing you at pickup. Ask
          it anything about sizing, colour or price, and it reads the same stock list our register
          does.
        </p>
        <p>
          Club orders, alumni reunions, family weekend, senior gifts, the sports team that just made
          the tournament and needs forty shirts by Thursday: that is the work we like best. Bring us a
          sketch on a napkin and we will tell you honestly whether it will print.
        </p>
      </div>

      <section className="numbers">
        {NUMBERS.map((item) => (
          <article key={item.label}>
            <p className="numbers__value">{item.value}</p>
            <p className="numbers__label">{item.label}</p>
          </article>
        ))}
      </section>

      <section className="cta">
        <h2>Come see what is on the rack</h2>
        <Link className="button button--solid button--lg" to="/products">
          Browse products
        </Link>
      </section>
    </div>
  );
}
