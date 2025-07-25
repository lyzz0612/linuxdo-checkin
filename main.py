"""
cron: 0 */6 * * *
new Env("Linux.Do 签到")
"""

import os
import random
import time
import functools
import sys
import requests
import re
from loguru import logger
from DrissionPage import ChromiumOptions, Chromium
from tabulate import tabulate

def retry_decorator(retries=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:
                        logger.error(f"函数 {func.__name__} 最终执行失败: {str(e)}")
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1}/{retries} 次尝试失败: {str(e)}"
                    )
                    time.sleep(1)
            return None
        return wrapper
    return decorator

os.environ.pop("DISPLAY", None)
os.environ.pop("DYLD_LIBRARY_PATH", None)

BROWSE_ENABLED = os.environ.get("BROWSE_ENABLED", "true").strip().lower() not in [
    "false", "0", "off"
]
GOTIFY_URL = os.environ.get("GOTIFY_URL")
GOTIFY_TOKEN = os.environ.get("GOTIFY_TOKEN")
SC3_PUSH_KEY = os.environ.get("SC3_PUSH_KEY")

HOME_URL = "https://linux.do/"

COOKIE_STR = "_ga=GA1.1.1194486217.1751335052; __stripe_mid=cac63275-1c52-495b-a516-25f8bb54de25b862ae; __stripe_sid=876730fb-97aa-4d76-a113-5be9db88be8363db12; cf_clearance=swqBKZ13bDnWEcDUQX60xAjTdnfAzFFVRls0iru.uow-1751335657-1.2.1.1-5Ad169h5GonP4kSk3aQ.ohHrvVFmHdx6.0wI3quXJ9Uvc8DVAG2utR3mbjJqCGVAq2depq1mmUDhj4NDENBDhXWuw2uafeu63LN5gXWlZ3KKwmA0rq26WQjzy2OWDxP743oHzNG2AKd2JkjN3PrAaurqID2FFKpWUXl9CIzpnZ65rQlA1T.jwrwGQQkn40HtyRFfXqSI96_n.i..emc0Gy87Ajbo6vkHS7lsd4.CfYwvv2MZ0rMGF.VwjNNzq_bzL.ZUPLQm0.VQ2vskKdnd1hZKCA.0I4R0PvAb1tOnHVognL6wTZmGBTpblMmZhcYLopS7he3gOh.w8PMgUOxuqaivYXEMMJL1i7ZuD_cP_zcprqJcq1SrnDGIbutMTmAX; _t=%2BVZqy5BOGt0577W6JaDYr3D2MKiYIJzhnhkMLqFiU%2BzkzfzrMPkAnRLjPsi0lxZP%2BZoGB%2Bwr0cX86ddoe8DpgxjdDsNaZjki2LLC7lnS4U%2FXm9g6GIMaIJODieylgYMVoJudxiH73aPwr9a1plDkvPJ%2BMUiT%2FxrvX%2BkhXIuyaO%2FRyvcsDr%2Bc7myhXBNNqbLkOQNJ2nP%2B4eyjot7hasElb4gIj94SahqwMyTEpQEpqECOC%2B7y4FCKSPm0ox%2B3Us2g9i4kgUWOkrHgMCzRLWf9IjQrw2s0LSqqTXGwvZGh2TgqrZV4EERNAOZHDB12XJTY--JPqPAkk4%2FdC5kqOu--MH7gVEULIY2weEabuFv%2BEw%3D%3D; _ga_1X49KS6K0M=GS2.1.s1751335052$o1$g1$t1751335677$j48$l0$h989914038; _forum_session=WdrL07jnUIxYCbUVdZGcv6N9jSkMsTp4nO6%2BMlC6K3ij3nOtc%2B1OMzKAX7wfsWKlnSuhbRGknKwBJoVf3VrBpztSgrLvRHOJ1O9ir1eVI3M1kpoMa9AiAPPjUfRa%2FA3DqTs5OvCuyTiZChiOvAcFelDIIvl4yq5nRsOhx0qXbRPadrwrX8sv36d4L2KCNO4CzTVrKrcK3iSsQZxqie%2F8ZXVzUor9WPUoWQLv0PN6ShMwI%2BPaDShWZQY0cUQSUddWdQjqTO4hpjUUNC0gdP%2BV0G1yPmMFI55I2mvjXDiYP772%2F25RnAJl8CuzxXykP7bmtpSQ1iHfQdvoZ%2B2ZyA7CTUuiOM7O8C%2Frg%2F9YEOZbiGcfXvg8fstfUVQ2l7ZaGw%3D%3D--N2CHpw1QZVYecLqQ--%2F3k4x0v5bQuYbKwGwRaPpg%3D%3D"

class LinuxDoBrowser:
    def __init__(self) -> None:
        EXTENSION_PATH = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "turnstilePatch")
        )
        from sys import platform
        if platform == "linux" or platform == "linux2":
            platformIdentifier = "X11; Linux x86_64"
        elif platform == "darwin":
            platformIdentifier = "Macintosh; Intel Mac OS X 10_15_7"
        elif platform == "win32":
            platformIdentifier = "Windows NT 10.0; Win64; x64"
        co = (
            ChromiumOptions()
            .headless(True)
            .add_extension(EXTENSION_PATH)
            .incognito(True)
            .set_argument("--no-sandbox")
        )
        co.set_user_agent(
            f"Mozilla/5.0 ({platformIdentifier}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )
        self.browser = Chromium(co)
        self.page = self.browser.new_tab()

    def set_cookies(self, cookies):
        # cookies: dict 类型
        for name, value in cookies.items():
            self.page.set.cookies({
                "name": name,
                "value": value,
                "domain": "linux.do",
                "path": "/"
            })

    def click_topic(self):
        topic_list = self.page.ele("@id=list-area").eles(".:title")
        logger.info(f"发现 {len(topic_list)} 个主题帖，随机选择10个")
        for topic in random.sample(topic_list, 10):
            self.click_one_topic(topic.attr("href"))

    @retry_decorator()
    def click_one_topic(self, topic_url):
        new_page = self.browser.new_tab()
        new_page.get(topic_url)
        if random.random() < 0.3:
            self.click_like(new_page)
        self.browse_post(new_page)
        new_page.close()

    def browse_post(self, page):
        prev_url = None
        for _ in range(10):
            scroll_distance = random.randint(550, 650)
            logger.info(f"向下滚动 {scroll_distance} 像素...")
            page.run_js(f"window.scrollBy(0, {scroll_distance})")
            logger.info(f"已加载页面: {page.url}")
            if random.random() < 0.03:
                logger.success("随机退出浏览")
                break
            at_bottom = page.run_js(
                "window.scrollY + window.innerHeight >= document.body.scrollHeight"
            )
            current_url = page.url
            if current_url != prev_url:
                prev_url = current_url
            elif at_bottom and prev_url == current_url:
                logger.success("已到达页面底部，退出浏览")
                break
            wait_time = random.uniform(2, 4)
            logger.info(f"等待 {wait_time:.2f} 秒...")
            time.sleep(wait_time)

    def run(self):
        cookies_str = os.environ.get("LINUXDO_COOKIES")
        if not cookies_str:
            cookies_str = COOKIE_STR

        if not cookies_str:
            logger.error("未配置 LINUXDO_COOKIES，程序终止")
            sys.exit(1)
        # 支持标准 cookie 字符串格式解析
        cookies = dict([item.strip().split("=", 1) for item in cookies_str.split(";") if "=" in item])

        logger.info("打开主页并注入 cookies 以实现免密登录")
        self.page.get(HOME_URL)
        self.set_cookies(cookies)
        self.page.refresh()
        time.sleep(2)

        # 检查是否登录成功（可根据页面元素灵活调整）
        if not self.page.ele("@id=current-user"):
            logger.error("登录失败，请检查 cookies 是否有效")
            sys.exit(1)
        logger.info("登录成功")

        if BROWSE_ENABLED:
            self.click_topic()
            logger.info("完成浏览任务")

        self.print_connect_info()
        self.send_notifications(BROWSE_ENABLED)
        self.page.close()
        self.browser.quit()

    def click_like(self, page):
        try:
            like_button = page.ele(".discourse-reactions-reaction-button")
            if like_button:
                logger.info("找到未点赞的帖子，准备点赞")
                like_button.click()
                logger.info("点赞成功")
                time.sleep(random.uniform(1, 2))
            else:
                logger.info("帖子可能已经点过赞了")
        except Exception as e:
            logger.error(f"点赞失败: {str(e)}")

    def print_connect_info(self):
        logger.info("获取连接信息")
        page = self.browser.new_tab()
        page.get("https://connect.linux.do/")
        rows = page.ele("tag:table").eles("tag:tr")
        info = []
        for row in rows:
            cells = row.eles("tag:td")
            if len(cells) >= 3:
                project = cells[0].text.strip()
                current = cells[1].text.strip()
                requirement = cells[2].text.strip()
                info.append([project, current, requirement])
        print("--------------Connect Info-----------------")
        print(tabulate(info, headers=["项目", "当前", "要求"], tablefmt="pretty"))
        page.close()

    def send_notifications(self, browse_enabled):
        status_msg = "✅每日登录成功"
        if browse_enabled:
            status_msg += " + 浏览任务完成"
        if GOTIFY_URL and GOTIFY_TOKEN:
            try:
                response = requests.post(
                    f"{GOTIFY_URL}/message",
                    params={"token": GOTIFY_TOKEN},
                    json={"title": "LINUX DO", "message": status_msg, "priority": 1},
                    timeout=10,
                )
                response.raise_for_status()
                logger.success("消息已推送至Gotify")
            except Exception as e:
                logger.error(f"Gotify推送失败: {str(e)}")
        else:
            logger.info("未配置Gotify环境变量，跳过通知发送")
        if SC3_PUSH_KEY:
            match = re.match(r"sct(\d+)t", SC3_PUSH_KEY, re.I)
            if not match:
                logger.error("❌ SC3_PUSH_KEY格式错误，未获取到UID，无法使用Server酱³推送")
                return
            uid = match.group(1)
            url = f"https://{uid}.push.ft07.com/send/{SC3_PUSH_KEY}"
            params = {"title": "LINUX DO", "desp": status_msg}
            attempts = 5
            for attempt in range(attempts):
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    logger.success(f"Server酱³推送成功: {response.text}")
                    break
                except Exception as e:
                    logger.error(f"Server酱³推送失败: {str(e)}")
                    if attempt < attempts - 1:
                        sleep_time = random.randint(180, 360)
                        logger.info(f"将在 {sleep_time} 秒后重试...")
                        time.sleep(sleep_time)

if __name__ == "__main__":
    l = LinuxDoBrowser()
    l.run()
