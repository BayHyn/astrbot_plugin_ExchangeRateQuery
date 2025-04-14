import aiohttp
from typing import Dict, Optional

class OpenExchangeRate:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.default_currency = "USD" # 免费api默认基准货币，兼容其他api(未测试)
        self.base_url = "https://openexchangerates.org/api/"
        self.session = aiohttp.ClientSession()

    async def check_usage_info(self) -> Optional[Dict]:
        """获取用户key信息"""
        url = f"{self.base_url}usage.json?app_id={self.api_key}"
        async with self.session.get(url) as resp:
            data = await self._handle_response(resp)
            return data

    async def fetch_latest_rates(self, base_currency: str = "USD") -> Dict[str, float]:
        """获取最新汇率"""
        url = f"{self.base_url}latest.json?app_id={self.api_key}"
        async with self.session.get(url) as resp:
            data = await self._handle_response(resp)
            data_default = data.get("rates", {})
            data_base = await self.base_rate_conversion(base_currency, data_default)
            return data_base

    async def fetch_historical_rates(
        self,
        base_currency: str,
        date: str
    ) -> Dict[str, float]:
        """获取历史汇率"""
        url = f"{self.base_url}historical/{date}.json?app_id={self.api_key}"
        async with self.session.get(url) as resp:
            data = await self._handle_response(resp)
            data_default = data.get("rates", {})
            data_base = await self.base_rate_conversion(base_currency, data_default)
            return data_base

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict:
        """统一处理API响应"""
        if response.status != 200:
            error = await response.text()
            raise Exception(f"API请求失败: {response.status} - {error}")
        return await response.json()

    async def base_rate_conversion(self, base_currency: str, data_default: list) -> dict:
        """将默认美元货币汇率转换为基础货币汇率"""
        if base_currency == self.default_currency:
            return data_default
        else:
            rate_dict = {}
            try:
                base_rate = data_default.get(base_currency)
                for key, value in data_default.items():
                    if key == base_currency:
                        rate_dict[self.default_currency] = 1.0 / base_rate
                    else:
                        rate_dict[key] = value / base_rate
                return rate_dict
            except Exception as e:
                print(f"获取{base_currency}汇率失败: {e}")
                return {}


    async def close(self):
        """关闭HTTP会话"""
        await self.session.close()
