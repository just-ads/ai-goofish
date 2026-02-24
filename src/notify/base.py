"""通知器基类 — 模板方法模式。

所有 Notifier 共享：
- 数据提取（从 TaskResult 中解析商品/分析字段）
- 消息渲染（支持用户自定义模板，回退到默认模板）
- 统一的 send / test 异常处理

子类只需实现 `_do_send` 和 `test`。
"""
from abc import ABC, abstractmethod

from src.types import TaskResult
from src.utils.logger import logger


class BaseNotifier(ABC):
    """通知器抽象基类。"""
    name: str = "Base"

    # 默认 Markdown 消息模板
    DEFAULT_TEMPLATE = (
        "**{title}** \n\n"
        "![]({image}) \n\n"
        "> 售价：{price}（原价：{origin_price}<br/>发货地：{location}<br/>推荐度：{score}<br/>AI分析：{reason} \n\n"
        "[查看商品]({link})"
    )

    def __init__(self, config: dict):
        self.message_template: str = config.get('message_template', '') or self.DEFAULT_TEMPLATE

    # ------------------------------------------------------------------
    # 公共方法
    # ------------------------------------------------------------------

    def send(self, task_result: TaskResult):
        """模板方法：提取数据 → 渲染消息 → 调用子类发送。"""
        try:
            logger.info(f"推送 [{self.name}] 通知")
            data = self._extract_data(task_result)
            message = self._render_message(data)
            self._do_send(data, message)
        except Exception as e:
            logger.error(f"[{self.name}] 通知失败: {e}")

    @abstractmethod
    def test(self):
        """发送测试通知，子类实现。"""
        ...

    # ------------------------------------------------------------------
    # 子类钩子
    # ------------------------------------------------------------------

    @abstractmethod
    def _do_send(self, data: dict, message: str):
        """实际发送逻辑，由子类实现。

        Args:
            data: _extract_data 返回的结构化字段字典。
            message: _render_message 渲染后的消息文本。
        """
        ...

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_data(task_result: TaskResult) -> dict:
        """从 TaskResult 提取通知所需的结构化字段。"""
        product = task_result["商品信息"]
        analysis = task_result.get("分析结果", {}) or {}
        images = product.get("商品图片列表", [])
        link = f"https://h5.m.goofish.com/item?id={product['商品ID']}"
        return {
            "title": str(product.get("商品标题", ""))[:20],
            "price": product.get("当前售价", ""),
            "origin_price": product.get("商品原价", ""),
            "location": product.get("发货地区", ""),
            "link": link,
            "reason": analysis.get("原因", ""),
            "score": analysis.get("推荐度", ""),
            "image": images[0] if images else "",
        }

    def _render_message(self, data: dict) -> str:
        """用模板 + 数据渲染最终消息文本。

        模板中可使用的占位符：
            {title}  {price}  {origin_price}  {location}
            {link}   {reason} {score}         {image}
        若自定义模板渲染失败，自动回退到默认模板。
        """
        try:
            return self.message_template.format(**data).strip()
        except (KeyError, ValueError, IndexError) as e:
            logger.warning(f"[{self.name}] 自定义模板渲染失败({e}), 使用默认模板")
            return self.DEFAULT_TEMPLATE.format(**data).strip()
