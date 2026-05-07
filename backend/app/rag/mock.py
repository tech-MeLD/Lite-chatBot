from app.rag.base import AbstractRAGClient


class MockRAGClient(AbstractRAGClient):
    def __init__(self):
        self._documents: list[str] = [
            "退货政策：支持7天无理由退货，商品需保持完好。退货请保留原包装和购物凭证。",
            "配送说明：全国包邮，默认使用顺丰快递，1-3个工作日送达。偏远地区可能延长1-2天。",
            "售后保障：所有商品享受1年质保。质保期内非人为损坏免费维修。",
            "支付方式：支持微信支付、支付宝、银行卡转账。大额支付需实名认证。",
            "客服工作时间：周一至周日 9:00-21:00，节假日另行通知。",
        ]

    async def search(self, query: str, top_k: int = 5) -> list[str]:
        query_lower = query.lower()
        results = []
        for doc in self._documents:
            if any(word in doc for word in query_lower.split()):
                results.append(doc)
        if not results:
            results = self._documents[:top_k]
        return results[:top_k]

    async def upload_document(self, content: str, metadata: dict | None = None) -> str:
        self._documents.append(content)
        return f"mock-doc-{len(self._documents)}"
