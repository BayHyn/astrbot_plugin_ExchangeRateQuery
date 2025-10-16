from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.core import AstrBotConfig
from astrbot.api import logger

from .OpenExchangeRate import OpenExchangeRate
from .src import EXCHANGE_RATE_TMPL

from datetime import datetime, timedelta
from typing import Any, List


@register(
    "astrbot_plugin_ExchangeRateQuery",
    "MoonShadow1976",
    "查询货币汇率的插件",
    "1.2.0",
    "https://github.com/MoonShadow1976/astrbot_plugin_ExchangeRateQuery",
)
class ExchangeRateQueryPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.api_key: str = config.get("api_key", "")
        self.past_day: int = config.get("past_day", 7)
        self.base_currency: str = config.get("base_currency", "CNY")
        self.default_currencies: list[str] = config.get(
            "target_currencies", ["USD", "RUB", "EUR", "JPY"]
        )
        self.enable_t2i: bool = config.get("enable_t2i", False)

        if not self.api_key:
            logger.error("未配置OpenExchangeRates API KEY!")

        self.client = OpenExchangeRate(self.api_key)


    @filter.command("汇率帮助", alias={"汇率查询"})
    async def exchange_query_help(self, event: AstrMessageEvent):
        """获取汇率查询帮助"""
        report = [
            "📅【汇率查询帮助】\n",
            "请先于控制台配置默认基准货币和目标货币\n",
            "默认查询命令：\n",
            "/汇率代码 :获取支持的货币代码与名称\n",
            "/汇率usage :查询key的健康值\n",
            "/汇率 :查询默认配置的汇率\n",
            "/汇率 USD JPY EUR :查询美元对日元和欧元的汇率\n",
        ]
        if self.enable_t2i:
            url = await self.text_to_image("\n".join(report))
            yield event.image_result(url)
        else:
            yield event.plain_result("\n".join(report))


    @filter.command("汇率代码", alias={"货币代码"})
    async def currencies_query(self, event: AstrMessageEvent):
        """获取支持的货币代码与名称"""
        currencies = await self.client.fetch_currencies()

        # 格式化货币代码输出
        formatted_currencies = "🏦【支持的货币代码】\n\n"
        for code, name in sorted(currencies.items()):
            formatted_currencies += f"• {code}: {name}\n\n"

        if self.enable_t2i:
            url = await self.text_to_image(formatted_currencies)
            yield event.image_result(url)
        else:
            yield event.plain_result(formatted_currencies)


    @filter.command("汇率usage", alias={"健康值"})
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
                "【OpenExchangeRates API 健康报告】\n",
                f"📊 套餐计划: {plan_data.get('name', '未知')}\n",
                f"🔢 更新频率: {plan_data.get('update_frequency', 0)}\n",
                f"📈 请求限额: {usage_data.get('requests_quota', 0)} 次/月\n",
                f"• 已用请求: {usage_data.get('requests', 0)} 次\n",
                f"• 剩余额度: {usage_data.get('requests_remaining', 0)} 次\n",
                f"• 本月已过: {usage_data.get('days_elapsed', 0)} 天\n",
                f"• 剩余天数: {usage_data.get('days_remaining', 0)} 天\n",
                f"📅 日均用量: {usage_data.get('daily_average', 0)} 次/天\n",
            ]

            # 计算健康指标
            remaining_percent = (
                usage_data.get("requests_remaining", 0)
                / usage_data.get("requests_quota", 1)
            ) * 100
            health_icon = (
                "✅"
                if remaining_percent > 20
                else "⚠️" if remaining_percent > 5 else "❌"
            )

            report.append(
                f"\n{health_icon} 健康状态: {remaining_percent:.1f}% 剩余额度"
            )

            if self.enable_t2i:
                url = await self.text_to_image("\n".join(report))
                yield event.image_result(url)
            else:
                yield event.plain_result("\n".join(report))

        except Exception as e:
            logger.error(f"健康值查询失败: {str(e)}")
            yield event.plain_result("获取健康值失败，请检查服务器日志")


    @filter.command("汇率", alias={"汇率查询"})
    async def exchange_rate_query(self, event: AstrMessageEvent):
        """查询货币汇率"""
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
            target_currencies = [
                c.upper() for c in parts[2:]
            ] or self.default_currencies

        try:
            # 获取支持的货币代码与名称
            currencies = await self.client.fetch_currencies()

            # 获取当前和一周前汇率
            current_date = datetime.now()
            week_ago = current_date - timedelta(days=self.past_day)

            current_rates = await self.client.fetch_latest_rates(base_currency)
            historical_rates = await self.client.fetch_historical_rates(
                week_ago.strftime("%Y-%m-%d"), base_currency
            )

            if self.enable_t2i:
                # 使用自定义HTML模板渲染图片
                html_data = self._format_html_comparison(
                    currencies,
                    base_currency,
                    current_rates,
                    historical_rates,
                    target_currencies,
                )
                try:
                    url = await self.html_render(EXCHANGE_RATE_TMPL, html_data)
                    yield event.image_result(url)
                except Exception as e:
                    logger.error(f"HTML渲染失败: {str(e)}")
                    # 生成对比结果
                    text_result = self._format_text_comparison(
                        currencies,
                        base_currency,
                        current_rates,
                        historical_rates,
                        target_currencies,
                    )
                    yield event.plain_result(text_result)
            else:
                # 生成对比结果
                text_result = self._format_text_comparison(
                    currencies,
                    base_currency,
                    current_rates,
                    historical_rates,
                    target_currencies,
                )
                yield event.plain_result(text_result)

        except Exception as e:
            logger.error(f"汇率查询失败: {str(e)}")
            yield event.plain_result("汇率查询失败，请稍后再试")


    def _format_text_comparison(
        self,
        currencies: dict[str, str],
        base: str,
        current: dict[str, float],
        historical: dict[str, float],
        targets: list[str],
    ) -> str:
        """格式化汇率对比结果为文本形式"""
        base_currency_name = currencies.get(base, base)
        result = [f"💱 【{base}({base_currency_name}) 汇率对比报告】"]
        result.append(f"📊 对比时间范围: {self.past_day}天前 vs 当前")
        result.append("")
        
        for currency in targets:
            curr_rate = current.get(currency)
            hist_rate = historical.get(currency)

            if curr_rate and hist_rate:
                change = curr_rate - hist_rate
                change_percent = (change / hist_rate) * 100
                arrow = "📈" if change > 0 else ("📉" if change < 0 else "➡️")
                trend = "上涨" if change > 0 else ("下跌" if change < 0 else "持平")
                
                currency_name = currencies.get(currency, currency)
                
                result.append(f"💰 {currency}({currency_name}):")
                result.append(f"   • 当前汇率: 1 {base} = {curr_rate:.4f} {currency}")
                result.append(f"   • {self.past_day}天前: 1 {base} = {hist_rate:.4f} {currency}")
                result.append(f"   • 变化: {arrow} {change:+.4f} ({change_percent:+.2f}%) {trend}")
                result.append("")

        if len(result) == 3:  # 只有标题和时间范围，没有有效数据
            result.append("❌ 未找到有效的汇率数据")

        return "\n".join(result)


    def _format_html_comparison(
        self,
        currencies: dict[str, str],
        base: str,
        current: dict[str, float],
        historical: dict[str, float],
        targets: list[str],
    ) -> dict[str, str | int | list[Any]]:
        """准备HTML模板渲染所需的数据"""
        base_currency_name = currencies.get(base, base)
        comparisons = []
        
        for currency in targets:
            curr_rate = current.get(currency)
            hist_rate = historical.get(currency)

            if curr_rate and hist_rate:
                change = curr_rate - hist_rate
                change_percent = (change / hist_rate) * 100
                trend = "up" if change > 0 else ("down" if change < 0 else "same")
                trend_text = "上涨" if change > 0 else ("下跌" if change < 0 else "持平")
                arrow = "↑" if change > 0 else ("↓" if change < 0 else "→")
                
                comparisons.append({
                    "currency_code": currency,
                    "currency_name": currencies.get(currency, currency),
                    "current_rate": f"{curr_rate:.4f}",
                    "historical_rate": f"{hist_rate:.4f}",
                    "change_value": f"{change:+.4f}",
                    "change_percent": f"{change_percent:+.2f}%",
                    "trend": trend,
                    "trend_text": trend_text,
                    "arrow": arrow
                })

        return {
            "base_currency": base,
            "base_currency_name": base_currency_name,
            "past_days": self.past_day,
            "comparisons": comparisons,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M")
        }


    async def terminate(self):
        await self.client.close()
        logger.info("货币汇率查询插件已安全停止")