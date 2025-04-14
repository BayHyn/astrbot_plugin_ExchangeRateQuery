from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.core import AstrBotConfig
from astrbot.api import logger

from .OpenExchangeRate import OpenExchangeRate

from datetime import datetime, timedelta
from typing import List

@register("exchange_rate", "ExchangeRateQuery", "查询货币汇率的插件", "1.0.0")
class ExchangeRateQueryPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.api_key: str = config.get("api_key", "")
        self.past_day: int = config.get("past_day", 7)
        self.base_currency: dict = config.get("base_currency", "CNY")
        self.default_currencies: List[str] = config.get("target_currencies", ["USD", "EUR", "JPY"])

        if not self.api_key:
            logger.error("未配置OpenExchangeRates API KEY!")

        self.client = OpenExchangeRate(self.api_key)


    @filter.command("exrate帮助", alias={"汇率查询"})
    async def exchange_query_help(self, event: AstrMessageEvent):
        yield event.plain_result("📅【汇率查询帮助】\n请先于控制台配置默认基准货币和目标货币\n默认查询命令：\n/usage :查询key的健康值\n/exrate :查询配置的汇率\n/exrate USD JPY :查询美元和日元的汇率")

    @filter.command("usage", alias={"健康值"})
    async def usage_query(self, event: AstrMessageEvent):
        """获取OpenExchangeRates API KEY健康值"""
        if not self.api_key:
            yield event.plain_result("控制台未配置API密钥")
            return

        try:
            # 获取API使用信息
            usage_info = await self.client.check_usage_info()
            logger.debug(f"查询usage: {usage_info}")

            # 安全获取数据字段
            data = usage_info.get("data", {})
            usage_data = data.get("usage", {})
            plan_data = data.get("plan", {})

            # 构建健康报告
            report = [
                "【OpenExchangeRates API 健康报告】",
                f"📊 套餐计划: {plan_data.get('name', '未知')}",
                f"🔢 更新频率: {plan_data.get('update_frequency', 0)}",
                "",
                f"📈 请求限额: {usage_data.get('requests_quota', 0)} 次/月",
                f"• 已用请求: {usage_data.get('requests', 0)} 次",
                f"• 剩余额度: {usage_data.get('requests_remaining', 0)} 次",
                f"• 本月已过: {usage_data.get('days_elapsed', 0)} 天",
                f"• 剩余天数: {usage_data.get('days_remaining', 0)} 天",
                f"📅 日均用量: {usage_data.get('daily_average', 0)} 次/天"
            ]

            # 计算健康指标
            remaining_percent = (usage_data.get("requests_remaining", 0) / usage_data.get("requests_quota", 1)) * 100
            health_icon = "✅" if remaining_percent > 20 else "⚠️" if remaining_percent > 5 else "❌"

            report.append(f"\n{health_icon} 健康状态: {remaining_percent:.1f}% 剩余额度")

            yield event.plain_result("\n".join(report))

        except Exception as e:
            logger.error(f"健康值查询失败: {str(e)}")
            yield event.plain_result("获取健康值失败，请检查服务器日志")

    @filter.command("exrate", alias={"汇率查询"})
    async def exchange_rate_query(self, event: AstrMessageEvent):
        """
        查询货币汇率
        格式：/exrate [基准货币] [目标货币]
        示例：/exrate USD JPY
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
            week_ago = current_date - timedelta(days=self.past_day)

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
        header = f"📈 【{base} 汇率对比报告】\n"
        separator = "\n"
        table_header = f"货币 | 当前汇率 | {self.past_day}天前   | 变化\n"

        rows = []
        for currency in targets:
            curr_rate = current.get(currency)
            hist_rate = historical.get(currency)

            if curr_rate and hist_rate:
                change = curr_rate - hist_rate
                arrow = "↑" if change > 0 else ("↓" if change < 0 else "→")
                row = (
                    f"{currency:3}| {curr_rate:.2f} | {hist_rate:.2f} | {change:.4f}{arrow}"
                )
                rows.append(row)

        if not rows:
            return "未找到有效的汇率数据"

        return header + separator + table_header + separator.join(rows) + separator

    async def terminate(self):
        await self.client.close()
        logger.info("货币汇率查询插件已安全停止")
