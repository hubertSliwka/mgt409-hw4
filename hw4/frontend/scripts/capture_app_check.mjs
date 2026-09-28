/**
 * Drive the running Campus Customs site with Chrome and save the app-check screenshots.
 *
 *   node scripts/capture_app_check.mjs
 *
 * Both servers must already be running: uvicorn on :8000 and vite on :5173.
 * Images land in ../output/app_check_images/.
 */

import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const HERE = dirname(fileURLToPath(import.meta.url));
const SHOTS = resolve(HERE, "../../output/app_check_images");
const SITE = process.env.SITE_URL ?? "http://localhost:5173";
const CHROME =
  process.env.CHROME_PATH ?? "C:/Program Files/Google/Chrome/Application/chrome.exe";
const TEST_USER = { email: "test@campuscustoms.yale.edu", password: "password" };
// Its M is at zero in the supplied inventory, which is what check 1 has to show.
const DETAIL_PRODUCT = process.env.DETAIL_PRODUCT ?? "crew-left-chest-hoodie";
const AGENT_TIMEOUT = 90_000;

const wait = (ms) => new Promise((done) => setTimeout(done, ms));

async function shoot(page, name) {
  const path = resolve(SHOTS, `${name}.png`);
  await page.screenshot({ path });
  console.log(`saved ${name}.png`);
}

async function assistantCount(page) {
  return page.$$eval(".bubble--assistant:not(.bubble--typing)", (nodes) => nodes.length);
}

async function ask(page, text, { expectCards = false } = {}) {
  const before = await assistantCount(page);
  await page.click(".chat-form input");
  await page.$eval(".chat-form input", (input) => {
    input.value = "";
  });
  await page.type(".chat-form input", text, { delay: 12 });
  await page.click(".chat-form button[type=submit]");
  await page.waitForFunction(
    (previous) =>
      document.querySelectorAll(".bubble--assistant:not(.bubble--typing)").length > previous,
    { timeout: AGENT_TIMEOUT },
    before,
  );
  if (expectCards) {
    await page.waitForSelector("[data-testid=chat-results]", { timeout: 15_000 });
  }
  await wait(700);
}

async function openChat(page) {
  if (await page.$(".chat-panel--open")) return;
  await page.waitForSelector(".chat-launcher:not(.chat-launcher--hidden)", { timeout: 30_000 });
  await page.click(".chat-launcher");
  await page.waitForSelector(".chat-panel--open", { timeout: 30_000 });
  await wait(400);
}

/** Scroll the transcript so the question and its answer are both in frame. */
async function frameLastExchange(page) {
  await page.evaluate(() => {
    const stream = document.querySelector(".chat-stream");
    if (!stream) return;
    const asked = [...stream.querySelectorAll(".bubble--user")].pop();
    if (asked) stream.scrollTop = Math.max(0, asked.offsetTop - stream.offsetTop - 16);
  });
  await wait(350);
}

async function clearGuestChat(page) {
  await page.evaluate(() => sessionStorage.removeItem("campus_customs_guest_chat"));
}

async function main() {
  await mkdir(SHOTS, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: "new",
    defaultViewport: { width: 1440, height: 950, deviceScaleFactor: 1.5 },
    args: ["--hide-scrollbars", "--force-color-profile=srgb"],
  });

  const page = await browser.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") console.log("page error:", message.text());
  });

  try {
    // 1. Storefront home.
    await page.goto(SITE, { waitUntil: "networkidle2" });
    await page.waitForSelector(".tile:not(.tile--skeleton)", { timeout: 30_000 });
    await wait(600);
    await shoot(page, "home");

    // 2. Products page with the search, category chips and sort controls in use.
    await page.goto(`${SITE}/products`, { waitUntil: "networkidle2" });
    await page.waitForSelector(".chip");
    await page.evaluate(() => {
      const chips = [...document.querySelectorAll(".chip")];
      const hoodie = chips.find((chip) => chip.textContent.trim().toLowerCase() === "hoodie");
      hoodie?.click();
    });
    await page.type(".filters input[type=search]", "navy", { delay: 20 });
    await page.waitForFunction(
      () => document.querySelectorAll(".tile--skeleton").length === 0,
      { timeout: 20_000 },
    );
    await wait(600);
    await shoot(page, "usability_filters");

    // 3. Chat search that puts product cards on the page, from a clean transcript.
    await page.goto(`${SITE}/products`, { waitUntil: "networkidle2" });
    await clearGuestChat(page);
    await page.reload({ waitUntil: "networkidle2" });
    await page.waitForSelector(".tile:not(.tile--skeleton)", { timeout: 30_000 });
    await openChat(page);
    await ask(page, "what hoodies do you have?", { expectCards: true });
    await frameLastExchange(page);
    await shoot(page, "chat_search_cards");

    // 4. Product detail: size picker showing real per-size stock.
    await page.goto(`${SITE}/products/${DETAIL_PRODUCT}`, { waitUntil: "networkidle2" });
    await page.waitForSelector(".sizes__row .size");
    await wait(500);
    await shoot(page, "product_detail_sizes");

    // 5. Chat checking the inventory level of the item on screen.
    await clearGuestChat(page);
    await page.reload({ waitUntil: "networkidle2" });
    await page.waitForSelector(".sizes__row .size");
    await openChat(page);
    await ask(page, "do you have this in M?");
    await frameLastExchange(page);
    await shoot(page, "chat_inventory");

    // 6. Signed-in shopper: say something worth remembering, leave, come back.
    await page.goto(`${SITE}/login`, { waitUntil: "networkidle2" });
    await page.type("input[type=email]", TEST_USER.email, { delay: 15 });
    await page.type("input[type=password]", TEST_USER.password, { delay: 15 });
    await Promise.all([
      page.click("button[type=submit]"),
      page.waitForFunction(() => document.querySelector(".nav__hello") !== null, {
        timeout: 20_000,
      }),
    ]);
    await openChat(page);
    await ask(page, "I wear a large and I'm after a navy crewneck for my mom");

    // Reload the whole site: the transcript has to come back from the database.
    await page.goto(`${SITE}/products`, { waitUntil: "networkidle2" });
    await page.waitForSelector(".tile:not(.tile--skeleton)", { timeout: 30_000 });
    await openChat(page);
    await page.waitForSelector(".bubble--user", { timeout: 20_000 });
    await ask(page, "what size did I say I wear?");
    await frameLastExchange(page);
    await shoot(page, "login_memory");

    console.log("app-check screenshots complete");
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
