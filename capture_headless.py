import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            # Using the system chromium-browser instead of playwright managed one
            browser = await p.chromium.launch(
                executable_path='/snap/bin/chromium',
                args=['--no-sandbox', '--disable-setuid-sandbox', '--headless']
            )
            page = await browser.new_page(viewport={'width': 1280, 'height': 800})
            await page.goto('http://localhost:5173')
            await asyncio.sleep(5) # Wait for animations and TMDB fetch
            await page.screenshot(path='/home/ubuntu/cinecal-web/screenshot.png', full_page=True)
            print("MEDIA:/home/ubuntu/cinecal-web/screenshot.png")
            await browser.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
