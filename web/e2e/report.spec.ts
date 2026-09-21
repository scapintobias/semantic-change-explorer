import { test, expect } from "@playwright/test";
test("real models load and semantic controls stay linked", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const external: string[] = [];
  page.on("request", (r) => {
    if (
      !r
        .url()
        .startsWith(process.env.SCE_REPORT_URL || "http://127.0.0.1:8765") &&
      !r.url().startsWith("data:")
    )
      external.push(r.url());
  });
  await page.goto("/");
  await expect(page.getByRole("status")).toContainText("Both states loaded");
  await expect(
    page.getByRole("heading", { name: "Service panel", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Lower housing mesh/ }).click();
  await expect(
    page.getByRole("heading", { name: "Lower housing", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("probable rename", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Ordered modifier stack", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "A only", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "A only", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "B only", exact: true }).click();
  await page.getByRole("slider").fill("0.7");
  await expect(
    page.getByRole("button", { name: "Compare", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("checkbox", { name: "Changed only" }).check();
  await page.getByLabel("Change category").selectOption("ambiguous");
  await expect(
    page.getByRole("navigation", { name: "Entities" }).getByRole("button"),
  ).toHaveCount(4);
  await page.getByLabel("Change category").selectOption("all");
  await page.getByRole("checkbox", { name: "Changed only" }).uncheck();
  await page.getByRole("button", { name: "Overlay", exact: true }).click();
  await page.getByRole("button", { name: /Service panel mesh/ }).click();
  await page.getByRole("button", { name: "Fit scene", exact: true }).click();
  await page.screenshot({ path: "../docs/demo.png", fullPage: true });
  await page.keyboard.press("]");
  await expect(
    page.getByRole("heading", { name: "Service panel", exact: true }),
  ).toHaveCount(0);
  // Raycasting must select a rendered entity, not merely set a test-side state.
  const canvas = page.locator("canvas");
  const bounds = await canvas.boundingBox();
  let selected = false;
  if (bounds)
    for (const [x, y] of [
      [0.5, 0.5],
      [0.45, 0.55],
      [0.55, 0.5],
      [0.4, 0.5],
      [0.6, 0.55],
    ]) {
      const old = await page.locator(".selection-head h1").textContent();
      await page.mouse.click(
        bounds.x + bounds.width * x,
        bounds.y + bounds.height * y,
      );
      if ((await page.locator(".selection-head h1").textContent()) !== old) {
        selected = true;
        break;
      }
    }
  expect(selected).toBeTruthy();
  expect(errors).toEqual([]);
  expect(external).toEqual([]);
});
