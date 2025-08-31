import aiohttp
from typing import Any, TypedDict


# 定义响应数据类型
class UsageInfo(TypedDict):
    status: dict[str, Any]
    data: dict[str, Any]


class ExchangeRatesResponse(TypedDict):
    disclaimer: str
    license: str
    timestamp: int
    base: str
    rates: dict[str, float]


class CurrencyInfo(TypedDict):
    code: str
    name: str


class OpenExchangeRate:
    def __init__(self, api_key: str):
        self.api_key: str = api_key
        self.default_currency: str = "USD"  # 免费api默认基准货币，兼容其他api(未测试)
        self.base_url: str = "https://openexchangerates.org/api/"
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def ensure_session(self):
        """确保会话已创建"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def check_usage_info(self) -> UsageInfo:
        """获取用户key信息"""
        await self.ensure_session()
        url = f"{self.base_url}usage.json?app_id={self.api_key}"
        async with self.session.get(url) as resp:
            data = await self._handle_response(resp)
            return data

    async def fetch_latest_rates(self, base_currency: str = "USD") -> dict[str, float]:
        """获取最新汇率"""
        await self.ensure_session()
        url = f"{self.base_url}latest.json?app_id={self.api_key}"
        async with self.session.get(url) as resp:
            data: ExchangeRatesResponse = await self._handle_response(resp)
            data_default = data.get("rates", {})
            data_base = await self.base_rate_conversion(base_currency, data_default)
            return data_base

    async def fetch_historical_rates(
        self, date_str: str, base_currency: str = "USD"
    ) -> dict[str, float]:
        """获取历史汇率

        Args:
            date_str: 历史日期，格式为YYYY-MM-DD
            base_currency: 基准货币代码，默认为USD
        """
        await self.ensure_session()
        url = f"{self.base_url}historical/{date_str}.json?app_id={self.api_key}"
        async with self.session.get(url) as resp:
            data: ExchangeRatesResponse = await self._handle_response(resp)
            data_default = data.get("rates", {})
            data_base = await self.base_rate_conversion(base_currency, data_default)
            return data_base

    async def fetch_currencies(self) -> dict[str, str]:
        """获取所有支持的货币代码及其名称

        返回示例:
            {
                "AED": "United Arab Emirates Dirham",
                "AFN": "Afghan Afghani",
                "ALL": "Albanian Lek",
                "AMD": "Armenian Dram"
            }
        """
        await self.ensure_session()
        url = f"{self.base_url}currencies.json?app_id={self.api_key}"
        async with self.session.get(url) as resp:
            data: CurrencyInfo = await self._handle_response(resp)
            return data

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Any:
        """统一处理API响应"""
        if response.status != 200:
            error = await response.text()
            raise Exception(f"API请求失败: {response.status} - {error}")
        return await response.json()

    async def base_rate_conversion(
        self, base_currency: str, data_default: dict[str, float]
    ) -> dict[str, float]:
        """将默认美元货币汇率转换为基础货币汇率"""
        if base_currency == self.default_currency:
            return data_default
        else:
            rate_dict = {}
            try:
                base_rate = data_default.get(base_currency)
                if base_rate is None:
                    raise ValueError(f"未找到基准货币 {base_currency} 的汇率")

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
        if self.session:
            await self.session.close()
