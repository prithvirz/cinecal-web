import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-setuid-sandbox'])
            page = await browser.new_page(viewport={'width': 1280, 'height': 800})
            await page.goto('http://localhost:5173')
            await asyncio.sleep(3) # Wait for animations
            await page.screenshot(path='/home/ubuntu/cinecal-web/screenshot.png', full_page=True)
            print("MEDIA:/home/ubuntu/cinecal-web/screenshot.png")
            await browser.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
