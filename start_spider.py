import asyncio

from src.spider.spider import main
from src.utils.logger import logger

if __name__ == "__main__":
    logger.info('------------------------------------- 爬虫开始运行 ---------------------------------------------')
    asyncio.run(main())
