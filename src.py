# 自定义HTML模板
EXCHANGE_RATE_TMPL = """
<div style="font-family: 'Microsoft YaHei', Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; min-height: 100vh;">
    <div style="background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin: 20px auto; max-width: 800px;">

        <!-- 标题区域 -->
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #2c3e50; margin: 0; font-size: 32px; font-weight: bold;">
                💱 汇率对比报告
            </h1>
            <div style="color: #7f8c8d; font-size: 18px; margin-top: 10px;">
                基准货币: <span style="color: #e74c3c; font-weight: bold;">{{ base_currency }}({{ base_currency_name }})</span>
            </div>
            <div style="color: #95a5a6; font-size: 16px; margin-top: 5px;">
                对比时间: {{ past_days }}天前 vs 当前
            </div>
        </div>

        <!-- 汇率对比表格 -->
        {% if comparisons %}
        <div style="margin-top: 20px;">
            {% for comp in comparisons %}
            <div style="background: {% if comp.trend == 'up' %}#e8f5e8{% elif comp.trend == 'down' %}#ffe8e8{% else %}#f8f9fa{% endif %}; 
                        border-left: 5px solid {% if comp.trend == 'up' %}#27ae60{% elif comp.trend == 'down' %}#e74c3c{% else %}#95a5a6{% endif %};
                        padding: 20px; margin: 15px 0; border-radius: 10px; transition: transform 0.2s;"
                 onmouseover="this.style.transform='translateX(5px)'" 
                 onmouseout="this.style.transform='translateX(0)'">

                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div>
                        <span style="font-size: 24px; font-weight: bold; color: #2c3e50;">
                            {{ comp.currency_code }}
                        </span>
                        <span style="color: #7f8c8d; margin-left: 10px;">{{ comp.currency_name }}</span>
                    </div>
                    <div style="font-size: 20px; font-weight: bold; 
                                color: {% if comp.trend == 'up' %}#27ae60{% elif comp.trend == 'down' %}#e74c3c{% else %}#95a5a6{% endif %};">
                        {{ comp.arrow }} {{ comp.change_percent }}
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
                    <div style="text-align: center;">
                        <div style="color: #7f8c8d; font-size: 14px;">当前汇率</div>
                        <div style="font-size: 20px; font-weight: bold; color: #2c3e50;">
                            {{ comp.current_rate }}
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #7f8c8d; font-size: 14px;">{{ past_days }}天前</div>
                        <div style="font-size: 18px; color: #95a5a6;">
                            {{ comp.historical_rate }}
                        </div>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 10px; color: #7f8c8d; font-size: 14px;">
                    变化值: <span style="color: {% if comp.trend == 'up' %}#27ae60{% elif comp.trend == 'down' %}#e74c3c{% else %}#95a5a6{% endif %}; 
                                   font-weight: bold;">{{ comp.change_value }}</span>
                    ({{ comp.trend_text }})
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div style="text-align: center; padding: 40px; color: #95a5a6;">
            <div style="font-size: 48px; margin-bottom: 20px;">❌</div>
            <div style="font-size: 20px;">未找到有效的汇率数据</div>
        </div>
        {% endif %}

        <!-- 页脚 -->
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #95a5a6; font-size: 14px;">
            更新时间: {{ update_time }}
        </div>
    </div>
</div>
"""
