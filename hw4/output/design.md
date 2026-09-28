# Design notes

What the storefront looks like, and why each choice is there to sell something.

## The idea

A campus print shop, not a licensing portal. The palette is Yale blue (`#00356B`) on warm
paper (`#F7F5EF`) with a brass accent (`#C8A951`) for the small signals — category eyebrows,
the "from our stock list" tag, the unread dot. Cold white was the first version and it looked
like an admin panel; the cream makes the navy feel like ink on a shop poster and gives the
product tiles something to sit on.

## Type

Fraunces for display, Inter for everything else. The serif does the collegiate work in the
headline and the product names without anyone having to write the word "tradition", and Inter
keeps prices, stock lines and form labels plain at small sizes. Prices are set in the serif
too, which quietly makes them read as part of the product rather than as a system number.

## Hierarchy

Every page opens with a brass eyebrow, a serif headline, then the thing itself. The hero is
split: copy on the left, a deep blue panel on the right with two slow-drifting shapes behind
the wordmark, so the page has movement before the shopper scrolls. Below it, three short
promises — printed locally, licensed, honest stock — because those are the three objections a
first-time visitor has.

Product tiles are a square image on a pale blue field, category, name, two clipped lines of
description, then the price in blue. Nothing else competes. The single-item page puts a
sticky image on the left and the decision on the right: price, description, facts, sizes,
actions — top to bottom in the order a shopper decides in.

## Motion

Tiles lift 4px and their image scales 4% on hover, so the grid feels like something you can
pick up. New tiles and chat bubbles fade up 10px on arrival. The chat panel opens with a
slight overshoot spring instead of a linear slide. Loading states shimmer rather than blank
out, so the page never looks broken. Everything motion-related is switched off under
`prefers-reduced-motion`.

## The chat, deliberately not a bolt-on

The panel uses the site's own palette, the same `ProductTile` component as the grid, and a
"from our stock list" tag when the answer came from the database. That tag is a design
decision with a business point: the reason to trust this widget over a generic chatbot is
that it is reading the shelf, so the interface says so. Assistant bubbles are cream with a
hairline border, the shopper's are solid navy, and the typing indicator is three dots at the
panel's own rhythm.

## The photography

The pack's product shots arrive pillarboxed: a white or black frame around the garment, at a
dozen different sizes. Serving those straight into a grid gave every third tile a black
border and made the page look broken rather than designed. The API now trims the dead bars
off a photo the first time it is asked for and caches the result, so the tiles read as one
set. Where the product itself is dark against a dark backdrop, the trim backs off and serves
the original instead of cutting into the garment.

## Why it should help sales

- The hero gives a first-time visitor two doors — browse, or ask — and the second one is the
  novelty, so it is a button, not a hint.
- Real stock counts on the size buttons remove the main reason to abandon a product page.
- The chat's product cards mean the answer to "what hoodies do you have?" is a row of things
  to click, not a paragraph to re-read, which shortens the path from question to product page.
- Honest sold-out states build the kind of trust that makes the second visit happen. A shop
  that tells you the medium is gone is a shop that is telling the truth about the large.
