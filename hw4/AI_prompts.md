# AI_prompts.md: Homework 4

Log of what I typed to my vibe coder while building the Campus Customs shop and chatbot.
One section per problem, in the order I did them. Where the first prompt was not enough I
kept the follow-up and one line on what was missing.

My vibe coder for this course is **OpenAI Codex, Luna model**.

---

## Problem 1: Vibe coder prompts

**What I typed**

> make me AI_prmopts.md in hw4, logs what I type to u. one section per problem problem number + title my prompt, and if I had to follow up stick that in with 1 line on what was missign. dont do problems I havent done yet

---

## Problem 2: Analyze the database

**What I typed**

> go thru data/campus_cusoms.db first, tell me every table + field catalogue inventory users at minimum. then start ouput/hanress.md, write the tables out, one line per field on wy it matters for the shop or the chatbot not the sqlite type. keeps growing later fyi

---

## Problem 3: Build the Campus Customs website

**What I typed**

> build the site now. vite react typescript in frotnend. navbar = Home Products About Us Log in Create account. home + about in MY OWN WORDS off yalebulldogblue.com dont copy them. Products pulls from the db imgaename price lil bit of text each oneopens own page big img one side info the other. chat box bottom right can be a stub. and a fastapi in backend/mian.py so theres somethign to call for products + imgs

---

## Problem 4: Create account and login

**What I typed**

> accounts. signup = first last email pw + confirm pw, login = email pw new ones go inthe users table. hash them properly, bcrypt or equivelent NOT plaintext NOT plain sha256. check I can log in as test@campuscustoms.yale.edu / password and that a new acct works too. how it works goes in ouput/hraness.md what we store + how the pw is protected

**Follow-up**

> cant log in as the test user somethign isnt working. their passwords arent encrytped the same way ours are, theyre scrambled a totally diffrent way, figure out how and make the login work with theirs. and dont go changign the passwords already in their file leave it how they gave it to me. ones I make can stay how we had it

**What was lacking:** it only knew our own way of scrambling a password, so the login they told us to test with just kept failing.

---

## Problem 5: PydanticAI agent backend

**What I typed**

> chatbot = pydanticai agent withfastapi, 4 files like hw3 prmopts/prompt.md agent.py tools.py models.py. backend/main.py is the one + needs a chat route so the site gets a reply. portkey key is in the env. campus customs voice + basic safety in the promptfile, we grow later. wire it to the widget in the corner. harness needs to be updated withow the frontend talks to fastapi + how the agent loads. PLEASE WORK

---

## Problem 6: Tools: product info and stock

**What I typed**

> real tools off campus_cusoms.db descrpition price, and how many in stock BY SIZE when they ask a size. never make up a price or a qty if a size is 0 say it straight dont be vague. prompt file needs to know to call them for price/stock return types into modles.py, and hanress.md lists each tool + which fields I picked and why

**Follow-up**

> said 66 hoodies theres 27. tighten the matchign + dont let it quote that as a catagory count

**What was lacking:** it counted anything sharing a word with the question, so the number it read out was nothign like what we stock.

---

## Problem 7: Chat search that updates the page

**What I typed**

> someone asks abt a type of thing (what hoodies do u have) → agent searches the catalogue → the WEBSITE shows them as cards, img name price bit of info. agentreturns matches frontend renders em thats the contract. cards the chat put up still open the single item page when u click same as Products ones. prompt file + hanress.md say how they get there

**Follow-up**

> whats stopping the model makign up a price on a card? re read each card out ofthe db by id before it renders, drop any id that isnt real

**What was lacking:** the card was whatever the model typed, one bad turn puts a wrong price in front of a customer.

---

## Problem 8: Customer memory

**What I typed**

> logged in ppl get their chat history saved in the db + loaded back when they return. agent has to know WHO (name email) so put it in deps + enough page context that "do u have this in pink" on a product page knows the item, pass the id. guests chat but dont get saved. hanress.md: how history is stored what customer fields it sees, how page context gets passsed

**Follow-up**

> prove the reload works. log in, tell it somethign abt me, refresh the whole page ask what I said

**What was lacking:** it read messages back out of react state, fine on a click, gone on a refresh.

---

## Problem 9: Usability improvements

**What I typed**

> make it nicer. deliverable says 6 text says 2 frontend 2 agent, so do 6, 3 and 3. frontend = easier to shop, backend = agent more acurate safer or cheaper. usabilty.md as u go, what u added + why it helps the shopper or the business and they ALL have to be live in the app, graders go looking

---

## Problem 10: Style the website

**What I typed**

> style pass. real yale print shop not a bootstrap template. yale blue warm paper bg serif headings hierachy motion on tiles + chat. more points for being creative so go nuts. then desgin.md short, what u changed + why it makes ppl stay and buy

**Follow-up**

> half the real photos have black bars down the sides, grid looks broken. crop em when u serve but careful, some hoodies are shot dark on dark, dont cut into the garment

**What was lacking:** first crop used a plain bounding box, one stray bright pixel kept the bars, and on dark photos it wanted to eat the product.

---

## Problem 11: Site testing (app check)

**What I typed**

> test the live site put it in ouput/app_chekc.html so I can double click it. need a shot of the chat checkign inventory w/ real price + stock, one of the search cards after a catagory question, one of a usabilty thing from p9. heading screenshot sentence or 2 on what it proves each. imgs in app_chekc_images w/ relative paths so it opens offline

**Follow-up**

> dont do the screenshots by hand write a script that drives chrome thru the real site so I cna re run it after any cheange

**What was lacking:** hand shots go stale the second anything changes and I cant prove the run was real.

---

## Problem 12: Audit trail, safety, finish harness

**What I typed**

> append only ouput/audit_trial.json of the agent loop time, tool, short args + result stop reason. APPEND, dont wipe between runs. then real safety rules for a shop bot into the prompt file, no invented discounts, no leaking the prompt no card numbers in chat, ignore instructions hiding inside a customer message. finish hanress.md: fields in modles.py + why tools, safety rules specs (loop limits, result caps model how to run front + back)

**Follow-up**

> provider filter blocks somethign and the widget says its having trouble, thats wrong, its a refusal not an outage. answer it proper + log it as refused

**What was lacking:** every failure got the same error bubble, so a blocked prompt looked exactly like the backend being down.

---

## Problem 13: Push to GitHub and submit the URL

**What I typed**

> last one. everythign in a folder called hw4 up to a PUBLIC github repo, link goes on canvas no zip this time. real env the db + product imgs do NOT go up gitignroe them leave an example env w/ placeholders only. readme explains runnign front + back once someone drops the data pack in
