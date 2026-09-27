# Campus Customs — shop + chatbot (MGT 409, Homework 4)

A Yale-apparel storefront with a PydanticAI shop assistant behind FastAPI. The chat reads the
same SQLite database the site does, so the prices and stock it quotes are the ones on the
shelf, and the products it finds appear on the page as clickable cards.

```
hw4/
├── AI_prompts.md            # what I typed to my vibe coder, one section per problem
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── frontend/                # Vite + React + TypeScript
│   ├── src/pages/           # Home, Products, ProductPage, About, Login, Signup
│   ├── src/components/      # NavBar, ProductTile, ChatWidget
│   ├── src/state/           # auth + page-context providers
│   └── scripts/             # capture_app_check.mjs, the browser-driven site test
├── backend/
│   ├── main.py              # FastAPI app — uvicorn main:app --reload --port 8000
│   ├── agent.py             # PydanticAI agent: model, deps, tool wiring
│   ├── tools.py             # database lookups + the append-only audit trail
│   ├── models.py            # Pydantic types shared by the API and the agent
│   ├── db.py                # schema-adaptive access to campus_customs.db
│   ├── security.py          # bcrypt password hashing, signed session tokens
│   └── prompts/prompt.md    # system prompt: voice, tool rules, safety rules
├── scripts/
│   └── seed_dev_data.py     # builds a local database when the data pack is absent
└── output/
    ├── harness.md           # how the whole system works
    ├── usability.md         # the six usability improvements
    ├── design.md            # design decisions
    ├── app_check.html       # site test with screenshots
    ├── app_check_images/
    └── audit_trail.json
```

The data pack is local only and is not in this repository:

```
hw4/data/
├── campus_customs.db
└── products/                # images the catalogue rows point at
```

## Run it

**1. Put the data pack in place.** Copy the course `campus_customs.db` to `hw4/data/` and the
product images to `hw4/data/products/`. The backend resolves the table and column names at
startup, so a pack that spells its columns differently still works — `GET /api/health` prints
what it found.

No pack on this machine? Build a development copy instead:

```
pip install -r requirements.txt
python scripts/seed_dev_data.py --data-dir data
```

It writes the same four tables (`catalogue`, `inventory`, `users`, `chat_messages`) from
`data/catalogue_seed.json` and draws a placeholder image per product, so every page and the
agent work end to end. Drop the real database in afterwards and it is used instead.

**2. Environment.** Copy `.env.example` to `.env` and set `PORTKEY_API_KEY` (or
`OPENAI_API_KEY`) and a `SESSION_SECRET`.

**3. Back end**, from the `backend/` folder:

```
cd backend
uvicorn main:app --reload --port 8000
```

**4. Front end**, in a second terminal:

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to port 8000.

## Accounts

The seeded pack includes `test@campuscustoms.yale.edu` / `password`. Creating an account
through the form works the same way; passwords are stored as bcrypt digests and the login
returns a signed 12-hour session token.

## Testing the agent without the browser

```
cd backend
python agent.py --message "what hoodies do you have?"
python agent.py --message "do you have this in M?" --product-id 17 --email test@campuscustoms.yale.edu
```

## Re-running the site test

With both servers up:

```
cd frontend
node scripts/capture_app_check.mjs
```

Chrome drives the real site and rewrites the screenshots in `output/app_check_images/` that
`output/app_check.html` links to. Set `CHROME_PATH` if Chrome is not at the default Windows
location.
