import json

from datetime import datetime
from typing import Dict, Any, List, Optional

from src.agent.client import AiClient
from src.utils.utils import dict_pick
from src.utils.logger import logger


class ProductEvaluator:
    """
    商品评估器：按步骤调用 AI
    """

    def __init__(self, client: AiClient, product: Dict[str, Any], seller: Dict[str, Any], history_prices: List | None, target_product: Dict[str, Any]):
        self.client = client
        self.product = product
        self.seller = seller
        self.target_product = target_product
        self.history_prices = history_prices
        self.history: List[Dict[str, Any]] = []

        logger.debug(f"ProductEvaluator 初始化: 商品ID={product.get('商品ID', '未知')}, 卖家ID={seller.get('卖家ID', '未知')}")

    async def _ask_ai(self, prompt: str, system_msg: Optional[str] = None) -> Dict[str, Any]:
        system_content = system_msg or (
            "你是商品建议度评估助手。输出必须是 JSON，不要有多余文本\n"
            "每个响应应包含字段：'analysis'(文字解释), 'suggestion'(0-100 的建议度), 'reason'(50-150个字的中文简短原因)"
        )
        message = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]

        logger.debug(f"调用AI: 提示长度={len(prompt)}")
        reply = await self.client.ask(message)

        try:
            parsed = json.loads(reply)
            if not isinstance(parsed, dict):
                logger.warning(f"AI返回非JSON对象: {reply[:100]}...")
                return {"error": "not_object", "raw": reply}

            suggestion = parsed.get('suggestion', 0)
            logger.debug(f"AI调用成功: suggestion={suggestion}")
            return parsed
        except Exception as e:
            logger.error(f"解析AI响应JSON失败: {e}, 原始响应: {reply[:200]}...")
            return {"error": "invalid_json", "raw": reply}

    async def step_title_filter(self) -> Dict[str, Any]:
        """步骤一：标题筛选，过滤不符合的商品"""
        logger.info(f"开始标题过滤: 目标商品={self.target_product.get('description', '未知')[:30]}...")

        prompt = (
            f"目标商品描述: {self.target_product.get('description')}\n"
            f"当前商品标题: {self.product.get('商品标题', '')[0:15]}\n\n"
            "任务：判断该商品标题是否符合目标商品。请给出清晰的分析(analysis)，并返回 'suggestion' 字段 (0-100) 和简短 'reason' (中文)\n\n"
            "示例输出:\n"
            '{"analysis":"标题包含关键字且型号匹配。", "suggestion": 90, "reason":"标题匹配目标商品"}'
        )
        reply = await self._ask_ai(prompt)

        suggestion = reply.get('suggestion', 0)
        if 'error' in reply:
            logger.error(f"标题过滤AI调用失败: {reply.get('error')}")
        else:
            logger.info(f"标题过滤完成: suggestion={suggestion}")

        self.history.append({"step": "标题过滤", "reply": reply})
        return reply

    async def step_seller_info(self) -> Dict[str, Any]:
        """步骤二：卖家可信度评估"""
        logger.info("开始卖家可信度评估")

        seller_info = self.seller.copy()
        seller_info.pop('卖家ID', None)

        prompt = (
            "根据以下卖家信息建立卖家画像，给出 0-100 的建议度(suggestion)，并提供清晰的分析(analysis)和简短原因(reason, 中文)\n"
            f"卖家信息: {json.dumps(seller_info, ensure_ascii=False)}\n\n"
            "示例输出:\n"
            '{"analysis": "卖家在售和已售数量高，回复率高", "suggestion": 80, "reason":"卖家信誉较好"}'
        )
        reply = await self._ask_ai(prompt)

        suggestion = reply.get('suggestion', 0)
        if 'error' in reply:
            logger.error(f"卖家评估AI调用失败: {reply.get('error')}")
        else:
            logger.info(f"卖家评估完成: suggestion={suggestion}")

        self.history.append({"step": "卖家评估", "reply": reply})
        return reply

    async def step_product(self, use_image: bool = False):
        logger.info(f"开始商品分析: use_image={use_image}")

        product = dict_pick(self.product, ['当前售价', '商品原价', '发布时间', '商品描述'])
        # if not use_image:
        #     product.pop("images", None)

        prompt = (
            f"上一步对卖家的分析结果：{json.dumps(self.history[-1].get('reply'), ensure_ascii=False)}\n\n"
            f"历史价格数据：{json.dumps(self.history_prices) if self.history_prices else 'null'}\n\n"
            f"当前时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n"
            f"目标商品描述: {self.target_product.get('description')}"
            "请结合卖家分析、目标商品描述和以下商品信息分析商品质量、可信度、商品符合度，给出 0-100 的建议度(suggestion)，并提供清晰的分析(analysis)和简短原因(reason, 中文)\n"
            f'商品信息：: {json.dumps(product, ensure_ascii=False)}\n\n'
            "示例输出:\n"
            '{"suggestion": 70, "analysis": "商家可信度高，商品质量良好，但描述不完全匹配", "reason":"基本符合购买需求"}'
        )
        reply = await self._ask_ai(prompt)

        suggestion = reply.get('suggestion', 0)
        if 'error' in reply:
            logger.error(f"商品分析AI调用失败: {reply.get('error')}")
        else:
            logger.info(f"商品分析完成: suggestion={suggestion}")

        self.history.append({"step": "商品分析", "reply": reply})
        return reply

    def synthesize_final(self) -> Dict[str, Any]:
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

        result = {
            "推荐度": score,
            "建议": verdict_text,
            "原因": final_analysis
        }

        logger.info(f"最终评估结果: 推荐度={score}, 建议={verdict_text}")
        return result

    async def evaluate(self, *, include_image: bool = False) -> Dict[str, Any]:
        """
        执行完整分析流程。
        """
        logger.info(f"开始商品评估流程: include_image={include_image}")
        self.history = []

        # Step 1: 如果标题不符合目标商品，直接返回
        step1 = await self.step_title_filter()
        if step1.get('suggestion') < 30:
            logger.warning(f"标题过滤未通过: suggestion={step1.get('suggestion')}, 提前结束评估")
            return self.synthesize_final()

        # Step 2: 分析卖家画像
        step2 = await self.step_seller_info()

        # 如果卖家建议度过低，不继续向下判断
        if step2.get('suggestion') < 50:
            logger.warning(f"卖家评估未通过: suggestion={step2.get('suggestion')}, 提前结束评估")
            return self.synthesize_final()

        # Step 3: 使用商品详情信息，商品图片(可选) 进行商品分析
        # todo 使用商品图片分析
        await self.step_product(include_image and False)

        logger.info("商品评估流程完成")
        return self.synthesize_final()
