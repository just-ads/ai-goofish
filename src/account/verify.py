import os

from src.env import STATE_FILE


async def verify_login():
    if not os.path.exists(STATE_FILE):
        return 0

    

    return 1

    '''
    async with create_browser(STATE_FILE) as p:
        page = await p.context.new_page()
        await page.goto(url='https://www.goofish.com/', wait_until="domcontentloaded")
        await page.wait_for_timeout(timeout=5_000)
        count = await page.locator(".header >> text=登录").count()
        if count == 0:
            return 1
        return -1
    '''
