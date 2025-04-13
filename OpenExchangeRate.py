# OpenExchangeRate.py
import aiohttp
from typing import Dict, Optional

class OpenExchangeRate:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openexchangerates.org/api/"
        self.session = aiohttp.ClientSession()

    async def fetch_latest_rates(self, base_currency: str = "USD") -> Dict[str, float]:
        """获取最新汇率"""
        url = f"{self.base_url}latest.json?app_id={self.api_key}&base={base_currency}"
        async with self.session.get(url) as resp:
            data = await self._handle_response(resp)
            return data.get("rates", {})

    async def fetch_historical_rates(
        self,
        base_currency: str,
        date: str
    ) -> Dict[str, float]:
        """获取历史汇率"""
        url = f"{self.base_url}historical/{date}.json?app_id={self.api_key}&base={base_currency}"
        async with self.session.get(url) as resp:
            data = await self._handle_response(resp)
            return data.get("rates", {})

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict:
        """统一处理API响应"""
        if response.status != 200:
            error = await response.text()
            raise Exception(f"API请求失败: {response.status} - {error}")
        return await response.json()

    async def close(self):
        """关闭HTTP会话"""
        await self.session.close()
