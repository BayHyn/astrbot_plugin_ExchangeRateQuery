from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.core import AstrBotConfig
from astrbot.api import logger

from .OpenExchangeRate import OpenExchangeRate

from datetime import datetime, timedelta
from typing import List, Tuple

@register("exchange_rate", "ExchangeRateQuery", "查询货币汇率的插件", "1.0.0")
class ExchangeRateQueryPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.api_key: str = config.get("api_key", "")
        self.fuzzy_match: int = config.get("fuzzy_match", True)
        self.base_currency: dict = config.get("base_currency", "USD")
        self.default_currencies: List[str] = config.get("target_currencies", ["CNY", "EUR", "JPY"])

        if not self.api_key:
            logger.error("未配置OpenExchangeRates API KEY!")

        self.client = OpenExchangeRate(self.api_key)


    @filter.command("exrate帮助", alias={"汇率查询"})
    async def exchange_query_help(self, event: AstrMessageEvent):
        yield event.plain_result("""
        【汇率查询帮助】
        请先于控制台配置默认基准货币和目标货币
        查询命令：/exrate
        """)

    @filter.command("exrate", alias={"汇率查询"})
    async def exchange_rate_query(self, event: AstrMessageEvent):
        """查询货币汇率
        格式：/exrate [基准货币] [目标货币1] [目标货币2]...
        示例：/exrate USD CNY JPY
        """
        if not self.api_key:
            yield event.plain_result("控制台未配置API密钥")
            return

        # 解析用户输入
        parts = event.message_str.strip().split()
        base_currency = self.base_currency
        target_currencies = self.default_currencies
        logger.info(f"查询汇率: 用户输入：{parts}")

        if len(parts) > 1:
            base_currency = parts[1].upper()
            target_currencies = [c.upper() for c in parts[2:]] or self.default_currencies

        try:
            # 获取当前和一周前汇率
            current_date = datetime.now()
            week_ago = current_date - timedelta(days=7)

            current_rates = await self.client.fetch_latest_rates(base_currency)
            historical_rates = await self.client.fetch_historical_rates(
                base_currency,
                week_ago.strftime("%Y-%m-%d")
            )

            # 生成对比结果
            result = self._format_comparison(
                base_currency,
                current_rates,
                historical_rates,
                target_currencies
            )

            yield event.plain_result(result)

        except Exception as e:
            logger.error(f"汇率查询失败: {str(e)}")
            yield event.plain_result("汇率查询失败，请稍后再试")

    def _format_comparison(
        self,
        base: str,
        current: dict,
        historical: dict,
        targets: List[str]
    ) -> str:
        """格式化汇率对比结果"""
        header = f"【{base} 汇率对比】\n"
        separator = "-" * 45 + "\n"
        table_header = "货币 | 当前汇率 | 一周前   | 变化\n"

        rows = []
        for currency in targets:
            curr_rate = current.get(currency)
            hist_rate = historical.get(currency)

            if curr_rate and hist_rate:
                change = curr_rate - hist_rate
                row = (
                    f"{currency:4} | {curr_rate:8.4f} | {hist_rate:8.4f} | "
                    f"{'+' if change >=0 else ''}{change:.4f}"
                )
                rows.append(row)

        if not rows:
            return "未找到有效的汇率数据"

        return header + separator + table_header + separator.join(rows) + separator

    async def terminate(self):
        await self.client.close()
        logger.info("货币汇率查询插件已安全停止")