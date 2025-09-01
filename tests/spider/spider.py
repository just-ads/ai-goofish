import unittest

from src.spider.spider import start_task


class SpiderTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_start_task(self):
        await start_task({
            "task_name": "test_task",
            "enabled": True,
            "keyword": "路由器",
            "max_pages": 2,
            "personal_only": False,
        })


if __name__ == '__main__':
    unittest.main()
