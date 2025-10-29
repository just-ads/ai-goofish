from typing import Dict, Any, List, Optional
import json

from src.agent.client import AiClient


class ProductEvaluator:
    """
    商品评估器：按步骤调用 AI
    """

    def __init__(self, client: AiClient, product: Dict[str, Any], seller: Dict[str, Any], target_product: Dict[str, Any]):
        self.client = client
        self.product = product
        self.seller = seller
        self.target_product = target_product
        self.history: List[Dict[str, Any]] = []
        self.result: Dict[str, Any] = {
            "steps": [],
            "verdict": None,
            "suggestion_score": 0,
            "final_analysis": None
        }

    async def _ask_ai(self, prompt: str, system_msg: Optional[str] = None) -> Dict[str, Any]:
        system_content = system_msg or (
            "你是商品建议度评估助手。输出必须是 JSON，不要有多余文本\n"
            "每个响应应包含字段：'analysis'(文字解释), 'suggestion'(0-100 的建议度), 'reason'(中文简短原因)"
        )
        message = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
        reply = await self.client.ask(message)
        try:
            parsed = json.loads(reply)
            if not isinstance(parsed, dict):
                return {"error": "not_object", "raw": reply}
            return parsed
        except Exception:
            return {"error": "invalid_json", "raw": reply}

    async def step_title_filter(self) -> Dict[str, Any]:
        """步骤一：标题筛选，过滤不符合的商品"""
        prompt = (
            f"目标商品描述: {self.target_product.get('description')}\n"
            f"当前商品标题: {self.product.get('商品标题', '')[0:15]}\n\n"
            "任务：判断该商品标题是否符合目标商品。请给出清晰的分析(analysis)，并返回 'suggestion' 字段 (0-100) 和简短 'reason' (中文)\n\n"
            "示例输出:\n"
            '{"analysis":"标题包含关键字且型号匹配。", "suggestion": 90, "reason":"标题匹配目标商品"}'
        )
        reply = await self._ask_ai(prompt)
        self.result["steps"].append({"step": "标题过滤", "reply": reply})
        return reply

    async def step_seller_info(self) -> Dict[str, Any]:
        """步骤二：卖家可信度评估"""
        seller_info = self.seller.copy()
        seller_info.pop('卖家ID', None)

        prompt = (
            "现在请根据以下卖家信息建立卖家画像，给出 0-100 的建议度(suggestion)，并提供清晰的分析(analysis)和简短原因(reason, 中文)\n"
            f"卖家信息: {json.dumps(seller_info, ensure_ascii=False)}\n\n"
            "示例输出:\n"
            '{"analysis": "卖家在售和已售数量高，回复率高", "suggestion": 80, "reason":"卖家信誉较好"}'
        )
        reply = await self._ask_ai(prompt)
        self.history.append({"step": "卖家评估", "reply": reply})
        score = 0
        if isinstance(reply, dict) and "suggestion" in reply:
            try:
                score = int(reply["suggestion"])
            except Exception:
                score = 0
        self.result["suggestion_score"] = score
        self.result["steps"].append({"step": "seller_info", "suggestion": score, "reply": reply})
        return reply

    async def step_product(self, use_image: bool = False):
        product = self.product.copy()
        if not use_image:
            product.pop("images", None)

        prompt = (
            f"这是上一步对卖家的分析结果：{json.dumps(self.history[0].get('reply'), ensure_ascii=False)}\n\n"
            f"这是目标商品描述: {self.target_product.get('description')}"
            "现在请结合卖家分析、目标商品描述和以下商品信息分析商品质量、可信度、商品符合度，给出 0-100 的建议度(suggestion)，并提供清晰的分析(analysis)和简短原因(reason, 中文)\n"
            f'商品信息：: {json.dumps(product, ensure_ascii=False)}\n\n'
            "示例输出:\n"
            '{"suggestion": 70, "analysis": "商家可信度高，商品质量良好，但描述不完全匹配", "reason":"基本符合购买需求"}'
        )
        reply = await self._ask_ai(prompt)
        self.history.append({"step": "product_info", "reply": reply})
        score = 0
        if isinstance(reply, dict) and "suggestion" in reply:
            try:
                score = int(reply["suggestion"])
            except Exception:
                score = 0
        self.result["suggestion_score"] = score
        self.result["steps"].append({"step": "商品评估", "suggestion": score, "reply": reply})
        return reply

    def synthesize_final(self) -> Dict[str, Any]:
        """
        parts: List[str] = []
        for step in self.result["steps"]:
            step_name = step.get("step")
            reply = step.get("reply", {})
            analysis = reply.get("analysis") if isinstance(reply, dict) else None
            if analysis:
                parts.append(f"{step_name}: {analysis}")
            else:
                fallback = (reply.get("reason") if isinstance(reply, dict) else None) or (reply.get("raw") if isinstance(reply, dict) else None)
                if fallback:
                    parts.append(f"{step_name}: {fallback}")
                else:
                    parts.append(f"{step_name}: 无可解析的分析输出")
        """

        last_step = self.result["steps"][-1]

        final_analysis = last_step.get('reply', {}).get('analysis', '')

        score = self.result["suggestion_score"]
        if score >= 80:
            verdict_text = "非常建议购买"
        elif score >= 60:
            verdict_text = "建议购买"
        elif score >= 30:
            verdict_text = "谨慎购买"
        else:
            verdict_text = "不建议购买"

        return {
            "推荐度": score,
            "建议": verdict_text,
            "原因": final_analysis
        }

    async def evaluate(self, *, include_image: bool = False) -> Dict[str, Any]:
        """
        执行完整分析流程。
        """
        self.history = []
        self.result = {"steps": [], "verdict": None, "suggestion_score": 0, "final_analysis": None}

        # Step 1: 如果标题不符合目标商品，直接返回
        step1 = await self.step_title_filter()
        if step1.get('suggestion') < 50:
            return {
                "verdict": 0,
                "verdictText": "不建议购买",
                "reason": "标题不符合目标商品，未进行详细分析"
            }

        # Step 2: 分析卖家画像
        step2 = await self.step_seller_info()

        # 如果卖家建议度过低，不继续向下判断
        if step2.get('suggestion') < 50:
            return self.synthesize_final()

        # Step 3: 使用商品详情信息，商品图片(可选) 进行商品分析
        # todo 使用商品图片分析
        await self.step_product(include_image and False)

        return self.synthesize_final()
