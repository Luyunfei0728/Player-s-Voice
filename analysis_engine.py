import pandas as pd
import requests
import json
import streamlit as st  # <--- 1. 新增：引入 streamlit 库

# 配置区
try:
    API_KEY = st.secrets["ZHIPU_API_KEY"]
except FileNotFoundError:
    # 这是一个容错，防止你在本地直接运行 python analysis_engine.py 时报错
    # 但在运行 streamlit run app.py 时，这里一定能取到值
    API_KEY = "未配置Key" 

API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL_NAME = "glm-4-flash" 

# --- 业务逻辑函数 ---

def calculate_keyword_frequency(df, keywords):
    """
    核心需求1 & 2：计算关键词出现频率
    返回字典: {'面包': 5, '西部': 2}
    """
    results = {}
    for word in keywords:
        count = df['Message'].str.contains(word, case=False, na=False).sum()
        results[word] = count
    return results

def extract_risk_messages(df):
    """
    核心需求3：风险预警雷达
    返回: 包含风险内容的 DataFrame
    """
    # 扩展了风险词库
    risk_keywords = [
        'bug', 'BUG', '卡顿', '闪退', '外挂', '脚本', '加速器', 
        '太难', '削弱', '不合理', '垃圾', '报错', 'ppt', 'PPT', 
        '数值崩坏', '无法登录'
    ]
    pattern = '|'.join(risk_keywords)
    # 筛选包含任意风险词的行
    risk_df = df[df['Message'].str.contains(pattern, case=False, na=False)].copy()
    return risk_df

def generate_context_summary(df, item_counts, risk_df):
    """
    数据压缩：将大量数据转化为简短的 Prompt 摘要喂给 AI
    """
    top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    risk_snippets = risk_df['Message'].head(5).tolist() if not risk_df.empty else ["无明显风险"]
    
    summary = f"""
    【数据统计摘要】
    - 数据集规模：{len(df)} 条对话。
    - 讨论热度Top3：{top_items}
    - 风险反馈数：{len(risk_df)} 条
    - 典型风险原声：{risk_snippets}
    """
    return summary

# --- AI 调用函数 (非流式) ---

def call_ai_analysis(messages):
    """
    同步调用 GLM-4 接口
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "stream": False # 明确关闭流式
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        resp_json = response.json()
        
        if "choices" in resp_json and len(resp_json["choices"]) > 0:
            return resp_json["choices"][0]["message"]["content"]
        return "API 返回为空，请检查。"
    except Exception as e:
        return f"AI 接口调用失败: {str(e)}"