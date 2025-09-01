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
            "risk_total": 0,
            "final_analysis": None
        }

    async def _ask_ai(self, prompt: str, system_msg: Optional[str] = None) -> Dict[str, Any]:
        system_content = system_msg or (
            "你是商品风险评估助手。输出必须是 JSON，不要有多余文本\n"
            "每个响应应包含字段：'analysis'(文字解释)\n"
            "根据任务类型可包含 'portrait'(卖家画像)、 'pass'(布尔)、'risk'(数值)、'reason'(简短原因)等"
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
        """步骤一：描述筛选，过滤不符合的商品"""
        prompt = (
            f"目标商品描述: {self.target_product.get('description')}\n"
            f"当前商品标题: {self.product.get('商品标题')}\n\n"
            "任务：判断该商品标题是否符合目标商品。请给出清晰的分析(analysis)，并返回布尔字段 'pass' 与简短 'reason'\n\n"
            "示例输出:\n"
            '{"analysis":"标题包含关键字且型号匹配。", "pass": true, "reason":"包含 iPhone 15 关键字"}'
        )
        reply = await self._ask_ai(prompt)
        self.result["steps"].append({"step": "title_filter", "reply": reply})
        return reply

    async def step_seller_info(self, simple: bool = True) -> Dict[str, Any]:
        """步骤二：卖家可信度评估"""
        seller_info = {
            "卖家个性签名": self.seller.get("卖家个性签名"),
            "卖家在售/已售商品数": self.seller.get("卖家在售/已售商品数"),
            "卖家收到的评价总数": self.seller.get("卖家收到的评价总数"),
            "好评率": self.seller.get("好评率"),
            "卖家信用等级": self.seller.get("卖家信用等级"),
            "注册时间": self.seller.get("注册时间"),
            "二十时小时回复率": self.seller.get("二十时小时回复率")
        } if simple else self.seller

        prompt = (
            "现在请根据以下卖家信息建立卖家画像，给出 0-100 的风险分(risk)，并提供清晰的分析(analysis)和卖家画像(portrait)\n"
            f"卖家信息: {json.dumps(seller_info, ensure_ascii=False)}\n\n"
            "要求：建立卖家画像\n\n"
            "示例输出:\n"
            '{"analysis": "卖家在售和已售数量高，二十时小时回复率高", "portrait":"商家、高信用等级、回复快", "risk": 50'
        )
        reply = await self._ask_ai(prompt)
        self.history.append({"step": "seller_info", "reply": reply})
        risk = 0
        if isinstance(reply, dict) and "risk" in reply:
            try:
                risk = int(reply["risk"])
            except Exception:
                risk = 0
        self.result["risk_total"] = risk
        self.result["steps"].append({"step": "seller_info", "risk": risk, "reply": reply})
        return reply

    async def step_product(self, use_image: bool = False):
        product = self.product.copy()
        if not use_image:
            product.pop("images")
        prompt = (
            f"这是上一步对卖家的分析结果：{json.dumps(self.history[0].get('reply'), ensure_ascii=False)}\n\n"
            f"这是目标商品描述: {self.target_product.get('description')}"
            "现在请结合卖家分析、目标商品描述和以下商品信息分析商品质量、可信度、商品符合度，给出 0-100 的风险分(risk)，并提供清晰的分析(analysis)\n"
            f'商品信息：: {json.dumps(product, ensure_ascii=False)}\n\n'
            "要求：分析商品质量和可信度\n\n"
            "示例输出:\n"
            '{"risk": 50, "analysis": "商家可信度高，商品质量良好，无维修，但是不完全满足目标商品描述"}'
        )
        reply = await self._ask_ai(prompt)
        self.history.append({"step": "seller_info", "reply": reply})
        risk = 0
        if isinstance(reply, dict) and "risk" in reply:
            try:
                risk = int(reply["risk"])
            except Exception:
                risk = 0
        self.result["risk_total"] = risk
        self.result["steps"].append({"step": "seller_info", "risk": risk, "reply": reply})
        return reply

    def synthesize_final(self) -> Dict[str, Any]:
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

        final_analysis = "；".join(parts) + f"；累计风险分: {self.result['risk_total']}。"

        if self.result["risk_total"] < 20:
            verdict = "建议购买"
        elif self.result["risk_total"] < 60:
            verdict = "谨慎购买"
        else:
            verdict = "不建议购买"

        self.result["final_analysis"] = final_analysis
        self.result["verdict"] = verdict
        return self.result

    async def evaluate(self, *, simple_seller: bool = True, include_image: bool = False) -> Dict[str, Any] | None:
        """
        执行完整分析流程。
        """
        self.history = []
        self.result = {"steps": [], "verdict": None, "risk_total": 0, "final_analysis": None}

        # Step 1 不是目标产品直接 pass 掉
        step1 = await self.step_title_filter()

        if step1.get('pass'):
            return None

        # Step 2 分析卖家画像
        step2 = await self.step_seller_info(simple_seller)

        # 如果卖家风险过高，不继续向下判断
        if step2.get('risk') > 60:
            return self.synthesize_final()

        # Step 3 使用商品详情信息，商品图片(可选) 进行商品分析
        await self.step_product(include_image)

        # 最终结论
        final = self.synthesize_final()
        return final
