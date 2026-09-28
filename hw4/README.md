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

**1. Put the data pack in place.** Unzip the course `data.zip` inside `hw4/`, so you end up
with `hw4/data/campus_customs.db` and `hw4/data/products/`. The backend resolves table and
column names at startup from `PRAGMA table_info`, which is how it reads this pack's
`product_id` slugs, `garment_type`, JSON `colors` and `search_tags`, and `image_file_path`
without any of those being hardcoded — `GET /api/health` prints what it found.

No pack on this machine? Build a development copy instead:

```
pip install -r requirements.txt
python scripts/seed_dev_data.py --data-dir data
```

It writes the same four tables (`catalogue`, `inventory`, `users`, `chat_messages`) and draws
a placeholder image per product, so every page and the agent work end to end. It reads its
product list from `data/catalogue_seed.json`, which lives under the gitignored `data/` folder
and is therefore not in this repository — with the course pack in place you do not need this
path at all. Drop the real pack in afterwards and it is used instead; the backend adapts to
whichever one is there.

**2. Environment.** Copy `.env.example` to `.env` and set `PORTKEY_API_KEY` (or
`OPENAI_API_KEY`) and a `SESSION_SECRET`. The backend reads `hw4/.env` and, if there is one,
the `.env` in the folder above it, so the key can be kept outside this folder entirely.

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

The pack ships `test@campuscustoms.yale.edu` / `password`, stored as a PBKDF2-SHA256 digest.
Login accepts that format and leaves it untouched. Accounts created through the form are
hashed with bcrypt. Either way the login returns a signed 12-hour session token, and no
password is ever stored in a readable form.

## Testing the agent without the browser

```
cd backend
python agent.py --message "what hoodies do you have?"
python agent.py --message "do you have this in M?" --product-id crew-left-chest-hoodie --email test@campuscustoms.yale.edu
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
