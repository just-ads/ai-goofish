import unittest

from src.spider.spider import main


class SpiderTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_main(self):
        await main(True)


if __name__ == '__main__':
    unittest.main()
