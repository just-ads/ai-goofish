import asyncio
import base64
import uuid
from typing import Any, Dict, Optional

from playwright.async_api import TimeoutError

from src.env import STATE_FILE
from src.utils.browser import create_browser

active_sessions: Dict[str, Dict[str, Any]] = {}
DEFAULT_LOGIN_TIMEOUT_SECONDS = 180
LOGIN_MODAL_SELECTOR = 'div[class*="login-modal-wrap"]'
LOGIN_FRAME_SELECTOR = "#alibaba-login-box"


async def _close_session(session_id: str) -> None:
    session = active_sessions.pop(session_id, None)
    if not session:
        return

    timeout_task = session.get("timeout_task")
    if timeout_task and not timeout_task.done() and timeout_task is not asyncio.current_task():
        timeout_task.cancel()

    manager = session.get("manager")
    if manager:
        await manager.stop()


async def close_login_session(session_id: str) -> bool:
    if session_id not in active_sessions:
        return False
    await _close_session(session_id)
    return True


def _schedule_session_timeout(session_id: str, timeout_seconds: int) -> asyncio.Task:
    async def _timeout_cleanup() -> None:
        try:
            await asyncio.sleep(timeout_seconds)
            await _close_session(session_id)
        except asyncio.CancelledError:
            return

    return asyncio.create_task(_timeout_cleanup())


async def _get_session(session_id: str) -> Dict[str, Any]:
    session = active_sessions.get(session_id)
    if not session:
        raise Exception(f"无效登录会话 {session_id}")
    return session


async def start_login(timeout_seconds: int = DEFAULT_LOGIN_TIMEOUT_SECONDS):
    timeout_seconds = max(10, int(timeout_seconds or DEFAULT_LOGIN_TIMEOUT_SECONDS))

    session_id = str(uuid.uuid4())
    manager = create_browser(STATE_FILE)

    try:
        p = await manager.start()

        page = await p.context.new_page()
        await page.goto("https://www.goofish.com", wait_until="domcontentloaded")

        timeout_task = _schedule_session_timeout(session_id, timeout_seconds)

        active_sessions[session_id] = {
            "manager": manager,
            "page": page,
            "timeout_task": timeout_task,
        }

        # 可能会自动弹出登录弹窗
        login_modal = page.locator(LOGIN_MODAL_SELECTOR)
        try:
            await login_modal.wait_for(state="visible", timeout=2_000)
        except TimeoutError:
            # 没自动弹出，手动点击登录
            try:
                login_btn = page.locator('div[class*="user-order-container"]').get_by_role("link", name="登录")
                await login_btn.click(timeout=500)
                await login_modal.wait_for(state="visible", timeout=500)
            # 可能已经登录了，登录并没有失效
            except TimeoutError:
                return {
                    "session_id": session_id,
                    "login_mode": "auto",
                    "timeout_seconds": timeout_seconds,
                }

        # 手机号登录的过期可能会自动登录，等待2s自动登录
        await page.wait_for_timeout(2_000)
        # 检查是否已经自动登录
        if not await login_modal.is_visible():
            return {
                "session_id": session_id,
                "login_mode": "auto",
                "timeout_seconds": timeout_seconds,
            }

        frame = page.frame_locator(LOGIN_FRAME_SELECTOR)

        # 可能有快速进入按钮
        try:
            quick_button = frame.get_by_text('快速进入')
            await quick_button.wait_for(state="visible", timeout=500)
            await quick_button.click()
            return {
                "session_id": session_id,
                "login_mode": "auto",
                "timeout_seconds": timeout_seconds,
            }
        except TimeoutError:
            pass

        active_sessions[session_id]["login_frame"] = frame

        agreement_checkbox = frame.locator("div.fm-agreement")
        if await agreement_checkbox.count() > 0:
            await agreement_checkbox.first.click()

        login_qr = frame.locator("#qrcode-img")
        await login_qr.wait_for(state="visible", timeout=5_000)
        image_bytes = await login_qr.screenshot()
        base64_str = base64.b64encode(image_bytes).decode("utf-8")

        return {
            "session_id": session_id,
            "login_mode": "manual",
            "qrcode": f"data:image/png;base64,{base64_str}",
            "timeout_seconds": timeout_seconds,
        }
    except Exception:
        await manager.stop()
        raise


async def send_sms_code(params: Dict[str, Any]) -> Dict[str, str]:
    session_id = params["session_id"]
    phone = params["phone"]
    session = await _get_session(session_id)

    login_frame = session.get("login_frame")
    if not login_frame:
        raise Exception("当前会话不支持短信验证码，请重新发起登录")
    sms_tab = login_frame.locator('a[class*="sms-login-tab-item"]')
    await sms_tab.click()

    phone_input = login_frame.locator('input[id="fm-sms-login-id"]')
    await phone_input.fill(phone)

    send_btn = login_frame.locator('div[class*="send-btn"]')
    await send_btn.click()

    return {"status": "sent"}


async def check_login(session_id: str) -> Dict[str, Optional[str]]:
    session = await _get_session(session_id)
    page = session["page"]
    login_frame = session.get("login_frame")

    login_modal = page.locator(LOGIN_MODAL_SELECTOR)
    modal_count = await login_modal.count()

    # 登录弹窗关闭(隐藏或移除)则视为登录成功
    if modal_count == 0 or not await login_modal.first.is_visible():
        await _close_session(session_id)
        return {"status": "success", "message": None}

    if login_frame:
        login_error = login_frame.locator("div[id='login-error']")
        if await login_error.count() > 0 and await login_error.first.is_visible():
            error_msg = (await login_error.first.inner_text()).strip() or "登录失败"
            return {"status": "error", "message": error_msg}

    return {"status": "pending", "message": None}


async def login(params: Dict[str, Any]):
    login_type = params["login_type"]
    session_id = params["session_id"]
    session = await _get_session(session_id)
    login_frame = session.get("login_frame")
    if not login_frame:
        raise Exception("当前会话不可提交账号登录，请重新发起登录")

    if login_type == "password":
        password_tab = login_frame.locator('a[class*="password-login-tab-item"]')
        await password_tab.click()

        user_input = login_frame.locator('input[id="fm-login-id"]')
        password_input = login_frame.locator('input[id="fm-login-password"]')
        await user_input.fill(params["username"])
        await password_input.fill(params["password"])

    elif login_type == "sms":
        sms_tab = login_frame.locator('a[class*="sms-login-tab-item"]')
        await sms_tab.click()

        phone_input = login_frame.locator('input[id="fm-sms-login-id"]')
        verify_code = login_frame.locator('input[id="fm-smscode"]')
        await phone_input.fill(params["phone"])
        await verify_code.fill(params["code"])

    elif login_type != "qr":
        raise Exception(f"不支持的登录方式: {login_type}")

    if login_type in {"password", "sms"}:
        submit_btn = login_frame.locator('button.sms-login, button.password-login')
        await submit_btn.click()

    return await check_login(session_id)
