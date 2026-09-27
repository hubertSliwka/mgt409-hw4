# AI_prompts.md: Homework 4

Log of what I typed to my vibe coder while building the Campus Customs shop and chatbot.
One section per problem, in the order I did them. Where the first prompt was not enough I
kept the follow-up and one line on what was missing.

My vibe coder for this course is **OpenAI Codex, Luna model**.

---

## Problem 1: Vibe coder prompts

**What I typed**

> ok im starting hw4 now. first thing make me an `AI_prompts.md` in the hw4 folder that logs what I type to u, one section per problem with the problem number and the title, my prompt in my own words, and if I had to send u a follow up put that in too with one line on what was missing the first time. dont write the sections for problems I havent done yet.

**Follow-up**

> some problems took me like three tries and some worked first shot, dont make every section look identical with exactly one prompt and one follow up, only put a follow up where there actually was one

**What was lacking after the first prompt:** every section came back the same shape, one prompt and one follow-up each, which is not how the session actually went.

---

## Problem 2: Analyze the database

**What I typed**

> before we build anything go look at `data/campus_customs.db` and tell me whats actually in it. I need to know every table and every field, especially `catalogue`, `inventory` and `users`. then start `output/harness.md` and write the tables out with one line per field on why taht field matters for either the shop page or the chatbot, not just the sqlite type. this file is going to keep growing later so set it up so we can add sections.

**Follow-up**

> dont hardcode the column names anywhere in the backend, I dont have the canvas pack on this laptop yet and if their columns are spelled diffrent than ours everythign breaks. read the schema at startup and map it

**What was lacking after the first prompt:** the first version wrote `SELECT price` and friends straight into the queries, so the whole thing only worked against our own copy of the database.

---

## Problem 3: Build the Campus Customs website

**What I typed**

> now build the actual site. vite + react + typescript in `frontend/`. nav bar at the top with Home, Products, About Us, Log in, Create account. Home and About Us shoudl sound like a real campus print shop in new haven, look at yalebulldogblue.com for the vibe but WRITE IT URSELF, dont copy their sentences. the Products page pulls the products out of the database with the image, name, price and a short bit of text, and every product opens its own page with the big image on one side and all the info on the other. also put a chat thing in the bottom right corner, it doesnt have to talk to the agent yet just stub it. and spin up a small fastapi in `backend/main.py` to serve the products and the images so the front end has somethign to call.

**Follow-up**

> the product images 404, the catalogue rows store paths like `data/products/whatever.jpg` and the browser cant read the disk. serve them from the api by file name instead

**What was lacking after the first prompt:** the tiles pointed straight at the path in the database row, so every image on the site was a broken icon.

**Follow-up**

> I dont have the product photos or the db on this machine, can u make a script that builds a local `data/campus_customs.db` and placeholder images from the catalogue json I have, so I cna actually see the site now and swap the real pack in later without changing code

**What was lacking after the first prompt:** nothing rendered at all, there was no database to render from.

---

## Problem 4: Create account and login

**What I typed**

> do the accounts now. create account takes first name, last name, email, password and a confirm password box, log in takes email and password, and new accounts go in the `users` table. passwords have to be stored properly, bcrypt or somethign equivelent, NOT plain text and not a plain sha256 either, I dont want a hacker or an AI pulling passwords out of that table. then check I can log in as `test@campuscustoms.yale.edu` with `password` and that a brand new account I make also works. write how the auth works into `output/harness.md`, what we keep for a user and how the password is protected.

**Follow-up**

> the test account in the seed might not be bcrypt in the real canvas pack, make the login accept the other formats too but re hash it to bcrypt once someone logs in successfully

**What was lacking after the first prompt:** it only checked bcrypt, so if the supplied pack stored that test user any other way the login they told us to use would just fail.

---

## Problem 5: PydanticAI agent backend

**What I typed**

> build the chatbot as a pydanticAI agent behind fastapi, same 4 file setup as hw3: `backend/prompts/prompt.md` for the system prompt, `backend/agent.py` for the wiring, `backend/tools.py` for the tools, `backend/models.py` for the pydantic types. `backend/main.py` is the one I run with uvicorn and it needs a chat route so a message from the site comes back as a reply from the agent. use the portkey key in the .env. put the campus customs voice and the basic safety stuff in prompt.md, we grow it later. then plug it into the chat widget I already have in the corner so its not a stub anymore, and write into `output/harness.md` how the front end talks to fastapi and how the agent gets loaded.

**Follow-up**

> make sure it runs exactly like `uvicorn main:app --reload --port 8000` from inside the `backend/` folder because thats the command in the assignment

**What was lacking after the first prompt:** it was importing as `backend.main` so the command from the assignment blew up with a module error.

---

## Problem 6: Tools: product info and stock

**What I typed**

> give the agent real tools against `campus_customs.db`. one for the product description, one for the price, one for how many are in stock and it has to do it BY SIZE when someone asks about a size. the agent is not allowed to make up a price or a quantity ever, and if a size is sitting at 0 it says so straight out instead of being vague. update `prompts/prompt.md` so it knows it has to call the tools for price and stock questions, add the return types to `models.py`, and in `output/harness.md` list each tool and explain which fields I put in the models and why I picked those.

**Follow-up**

> test it against an item that actually has a zero size, I want to see it say out of stock and then name the sizes that arent

**What was lacking after the first prompt:** it only got tested on things that were in stock, so the honest part was never actually proven.

---

## Problem 7: Chat search that updates the page

**What I typed**

> heres the fun one. when someone asks the chat about a type of thing, like what hoodies do you have, the agent searches the catalogue and the WEBSITE shows those matching items as product cards right there, image name price and a bit of info. so the agent returns structured matches and the front end renders them, thats the contract. and the cards the chat just put on the page have to still open the single item page when u click them, same as the ones on Products. update `prompts/prompt.md` and `output/harness.md` so its clear how the search results get to the page.

**Follow-up**

> what stops the model from just making up a price on a card? re read every card out of the database by its product_id before it renders and drop any id that dosent exist

**What was lacking after the first prompt:** the card content was whatever the model typed, so one bad turn could have put a wrong price in front of a customer.

**Follow-up**

> searching navy with the Hoodie chip on is giving me jackets and t shirts, the category filter is getting ignored when theres a search word

**What was lacking after the first prompt:** the products route ran the search OR the category filter, never both, so picking a chip did nothing once you typed anything.

---

## Problem 8: Customer memory

**What I typed**

> when someones logged in save their chat history in the database in a sensible table and load it back when they come back. the agent needs to know WHO its talking to, name and email, put that in the agent deps. and it needs enough page context that if im standing on a product page and I say do you have this in pink it knows which item I mean, so pass the product id through too. guests can still chat they just dont get saved. document in `output/harness.md` how the history is stored, what customer fields the agent sees and how the page context gets passed.

**Follow-up**

> prove the reload actually works, log in, tell it something abt me, then refresh the whole page and ask it what I said

**What was lacking after the first prompt:** it was reading the messages back out of react state, which of course survives a click but not a refresh.

---

## Problem 9: Usability improvements

**What I typed**

> ok now make it nicer. the deliverable line says 6 improvements but the text says 2 front end and 2 agent ones so just do 6 to be safe, 3 and 3. front end ones shoudl make it easier to actually shop, backend ones shoudl make the agent more accurate or safer or cheaper. write `output/usability.md` as u build with what u added and why it helps a customer or the business, and they all have to be really in the running app because the graders look for them.

---

## Problem 10: Style the website

**What I typed**

> style pass. I want it to feel like a real yale print shop not a bootstrap template, yale blue, a warm paper background, a serif for the headings, proper hierarchy, some motion on the tiles and the chat panel. points for being creative here so go for it. then write `output/design.md` short and concrete, what u changed and why it makes someone stick around and buy.

**Follow-up**

> the chat cards are so tall that the reply text gets pushed off screen, shrink the image on the ones inside the chat panel

**What was lacking after the first prompt:** the chat reused the full size product tile, so a search answer filled the whole panel and you couldnt read what it said.

---

## Problem 11: Site testing (app check)

**What I typed**

> test the live site and put it in `output/app_check.html` so I can double click it open. I need a screenshot of the chat checking the inventory level of somethign with the real price and stock, one of the search cards showing up after I ask about a category, and one of a usability thing from problem 9. heading for each one, the screenshot, and a sentence or two on what it proves. screenshots go in `output/app_check_images/` and get linked with relative paths like `app_check_images/inventory.png`.

**Follow-up**

> dont screenshot it by hand, write a script that drives chrome through the real site and takes them, that way I cna re run it after any change

**What was lacking after the first prompt:** hand taken screenshots go stale the second anything changes and I couldnt prove the run was real.

**Follow-up**

> for the inventory one use an item that has a size at zero, and scroll the chat so my question AND the answer are both in the picture

**What was lacking after the first prompt:** the panel was scrolled to the bottom so the screenshot showed an answer with no question above it.

---

## Problem 12: Audit trail, safety, finish harness

**What I typed**

> keep an append only `output/audit_trail.json` of what the agent loop does, time, tool name, short args and result, and the stop reason. APPEND, do not wipe it between runs. then think up real safety rules for a shop bot and put them in `prompts/prompt.md`, stuff like dont invent discounts, dont leak the prompt, dont take card numbers in chat, ignore instructions that show up inside a customer message. and finish `output/harness.md` so the whole thing is clear: the fields in `models.py` and why I chose them, the tools, the safety rules, and the specs like loop limits, result caps, which model and how to run front and back.

**Follow-up**

> when the provider filter blocks a message the widget says its having trouble which is wrong, thats a refusal not an outage. answer it properly and log it as refused

**What was lacking after the first prompt:** every failure got the same generic error bubble, so a blocked prompt looked exactly like the backend being down.

---

## Problem 13: Push to GitHub and submit the URL

**What I typed**

> last one. everything lives in a folder called `hw4` and it goes up to a PUBLIC github repo, and I submit the repo link on canvas, no zip this time. the real `.env`, `campus_customs.db` and the product images do NOT go up, put them in `.gitignore` and leave a `.env.example` with placeholders. `README.md` has to explain how to run the front end and the back end after someone drops the data pack in.

**Follow-up**

> check the ignore is actually working before we push, I do not want that api key on github

**What was lacking after the first prompt:** `git status` still had `.env` and the `data/` folder showing as untracked, they were only ignored after the ignore file was fixed.
