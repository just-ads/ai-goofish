import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.types import Product, Seller, ProductPriceData, Analysis
from src.utils.logger import logger
from src.utils.utils import dict_pick


class ProductEvaluator:
    """
    商品评估器：按步骤调用 AI
    """

    def __init__(self, text_ai_client, image_ai_client):
        self.history: List[Dict[str, Any]] = []
        self.text_ai_client = text_ai_client
        self.image_ai_client = image_ai_client
        logger.debug("ProductEvaluator 初始化完成")

    async def _ask_ai(self, prompt: str, system_msg: Optional[str] = None) -> Dict[str, Any]:
        ai_client = self.text_ai_client.get_text_client()
        if ai_client is None:
            raise RuntimeError("无法获取AI客户端，请检查Agent配置")

        system_content = system_msg or (
            "你是商品建议度评估助手。输出必须是 JSON，不要有多余文本\n"
            "每个响应应包含字段：'analysis'(文字解释), 'suggestion'(0-100 的建议度), 'reason'(50-150个字的中文简短原因)"
        )

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]

        logger.debug(f"调用AI: 提示长度={len(prompt)}")
        response = await ai_client.ask(messages=messages)

        if not response.success:
            logger.error(f"AI调用失败: {response.error}")
            raise RuntimeError(f"AI调用失败: {response.error}")

        try:
            if not response.content:
                raise ValueError("AI返回空内容")

            parsed = json.loads(response.content)
            if not isinstance(parsed, dict):
                logger.warning(f"AI返回非JSON对象: {response.content[:100]}...")
                raise ValueError(f"AI返回非JSON对象: {response.content[:100]}...")

            suggestion = parsed.get('suggestion', 0)
            logger.debug(f"AI调用成功: suggestion={suggestion}")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(
                f"解析AI响应JSON失败: {e}, 原始响应: {response.content[:200] if response.content else '空响应'}...")
            raise ValueError(f"解析AI响应JSON失败: {e}")
        except Exception as e:
            logger.error(f"处理AI响应失败: {e}")
            raise RuntimeError(f"处理AI响应失败: {e}")

    async def step_title_filter(self, product: Product, target_product: Dict[str, Any]) -> Dict[str, Any]:
        """步骤一：标题筛选，过滤不符合的商品"""
        logger.info(f"开始标题过滤: 目标商品={target_product.get('description', '未知')[:30]}...")

        prompt = (
            f"目标商品描述: {target_product.get('description')}\n"
            f"当前商品标题: {product.get('商品标题', '')[0:15]}\n\n"
            "任务：判断该商品标题是否符合目标商品。请给出清晰的分析(analysis)，并返回 'suggestion' 字段 (0-100) 和简短 'reason' (中文)\n\n"
            "示例输出:\n"
            '{"analysis":"标题包含关键字且型号匹配。", "suggestion": 90, "reason":"标题匹配目标商品"}'
        )
        reply = await self._ask_ai(prompt)

        suggestion = reply.get('suggestion', 0)
        logger.info(f"标题过滤完成: suggestion={suggestion}")

        self.history.append({"step": "标题过滤", "reply": reply})
        return reply

    async def step_seller_info(self, seller: Seller) -> Dict[str, Any]:
        """步骤二：卖家可信度评估"""
        logger.info("开始卖家可信度评估")

        seller_info = seller.copy()
        seller_info.pop('卖家ID', None)

        prompt = (
            "根据以下卖家信息建立卖家画像，给出 0-100 的建议度(suggestion)，并提供清晰的分析(analysis)和简短原因(reason, 中文)\n"
            f"卖家信息: {json.dumps(seller_info, ensure_ascii=False)}\n\n"
            "示例输出:\n"
            '{"analysis": "卖家在售和已售数量高，回复率高", "suggestion": 80, "reason":"卖家信誉较好"}'
        )
        reply = await self._ask_ai(prompt)

        suggestion = reply.get('suggestion', 0)
        logger.info(f"卖家评估完成: suggestion={suggestion}")

        self.history.append({"step": "卖家评估", "reply": reply})
        return reply

    async def step_product(self, product: Product, target_product: Dict[str, Any], history_prices: List | None,
                           use_image: bool = False):
        logger.info(f"开始商品分析: use_image={use_image}")

        product_info = dict_pick(dict(product), ['当前售价', '商品原价', '发布时间', '商品描述'])
        # if not use_image:
        #     product_info.pop("images", None)

        prompt = (
            f"上一步对卖家的分析结果：{json.dumps(self.history[-1].get('reply'), ensure_ascii=False)}\n\n"
            f"历史价格数据：{json.dumps(history_prices, ensure_ascii=False) if history_prices else 'null'}\n\n"
            f"当前时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n"
            f"目标商品描述: {target_product.get('description')}"
            "请结合卖家分析、目标商品描述和以下商品信息分析商品质量、可信度、商品符合度，给出 0-100 的建议度(suggestion)，并提供清晰的分析(analysis)和简短原因(reason, 中文)\n"
            f'商品信息：: {json.dumps(product_info, ensure_ascii=False)}\n\n'
            "示例输出:\n"
            '{"suggestion": 70, "analysis": "商家可信度高，商品质量良好，但描述不完全匹配", "reason":"基本符合购买需求"}'
        )
        reply = await self._ask_ai(prompt)

        suggestion = reply.get('suggestion', 0)
        logger.info(f"商品分析完成: suggestion={suggestion}")

        self.history.append({"step": "商品分析", "reply": reply})
        return reply

    def synthesize_final(self) -> Analysis:
        last_step = self.history[-1] if self.history else {}
        reply = last_step.get('reply', {})
        final_analysis = reply.get('analysis', '')
        score = reply.get('suggestion', 0)

        if score >= 80:
            verdict_text = "非常建议购买"
        elif score >= 60:
            verdict_text = "建议购买"
        elif score >= 30:
            verdict_text = "谨慎购买"
        else:
            verdict_text = "不建议购买"

        result: Analysis = {
            "推荐度": score,
            "建议": verdict_text,
            "原因": final_analysis
        }

        logger.info(f"最终评估结果: 推荐度={score}, 建议={verdict_text}")
        return result

    async def evaluate(
            self,
            product: Product,
            seller: Seller,
            history_prices: List[ProductPriceData] | None,
            target_product: Dict[str, Any],
            *,
            include_image: bool = False
    ) -> Analysis:
        """
        执行完整分析流程。
        """
        logger.info(f"开始商品评估流程: include_image={include_image}")
        self.history = []

        # Step 1: 如果标题不符合目标商品，直接返回
        step1 = await self.step_title_filter(product, target_product)
        suggestion1 = step1.get('suggestion', 0)
        if suggestion1 < 30:
            logger.warning(f"标题过滤未通过: suggestion={suggestion1}, 提前结束评估")
            return self.synthesize_final()

        # Step 2: 分析卖家画像
        step2 = await self.step_seller_info(seller)

        # 如果卖家建议度过低，不继续向下判断
        suggestion2 = step2.get('suggestion', 0)
        if suggestion2 < 50:
            logger.warning(f"卖家评估未通过: suggestion={suggestion2}, 提前结束评估")
            return self.synthesize_final()

        # Step 3: 使用商品详情信息，商品图片(可选) 进行商品分析
        # todo 使用商品图片分析
        await self.step_product(product, target_product, history_prices, include_image and False)

        logger.info("商品评估流程完成")
        return self.synthesize_final()
