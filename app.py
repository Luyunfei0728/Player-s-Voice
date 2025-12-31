import streamlit as st
import pandas as pd
import plotly.express as px

# 引入模块
import data_loader
import analysis_engine as engine

# --- 页面配置 ---
st.set_page_config(page_title="玩家之声 - 舆情分析 Pro", layout="wide")
st.title("🎮 “玩家之声” 游戏舆情智能分析助手 (Pro Ver.)")

# --- 1. 数据加载 ---
with st.sidebar:
    st.header("🗂️ 数据控制台")
    uploaded_file = st.file_uploader("上传聊天日志", type="txt")
    
    if uploaded_file:
        raw_content = uploaded_file.getvalue().decode("utf-8")
        df = data_loader.parse_chat_log(raw_content)
        st.success(f"已加载 {len(df)} 条记录")
    else:
        df = data_loader.load_demo_data()
        st.info("当前运行模式：演示数据")

# --- 2. 业务指标计算 (Model) ---
new_items_list = ['面包', '爆米花', '浴桶', '肥皂', '仙人掌', '斐济杯', '喷气背包', '猫']
gameplay_list = ['西部', '唐人街', '精神病', '肉鸽', '飞船', '开局', '召唤']

item_counts = engine.calculate_keyword_frequency(df, new_items_list)
gameplay_counts = engine.calculate_keyword_frequency(df, gameplay_list)
risk_df = engine.extract_risk_messages(df)

# --- 3. 核心功能可视化 (View) ---

tab1, tab2, tab3 = st.tabs(["🛠️ 新变化风向标", "🔥 玩法热度监测", "🚨 风险预警雷达"])

with tab1:
    col_a, col_b = st.columns([2, 1])
    with col_a:
        item_df = pd.DataFrame(list(item_counts.items()), columns=['Item', 'Count']).sort_values('Count', ascending=False)
        fig = px.bar(item_df, x='Item', y='Count', color='Count', title="新装备讨论热度排行")
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        st.markdown("### 🤖 AI 情感速评")
        # 安全获取 Top 1，防止数据为空报错
        if not item_df.empty:
            top_item = item_df.iloc[0]['Item']
            if st.button(f"分析玩家对“{top_item}”的态度"):
                with st.spinner("AI 正在阅读相关评论..."):
                    msgs = [{"role": "user", "content": f"请阅读数据，用一句话总结玩家对装备'{top_item}'的情感倾向（喜欢还是讨厌？为什么？）"}]
                    related_msgs = df[df['Message'].str.contains(top_item, na=False)]['Message'].tolist()
                    msgs[0]['content'] += f"\n相关评论参考：{str(related_msgs[:10])}"
                    
                    ai_comment = engine.call_ai_analysis(msgs)
                    st.info(ai_comment)
        else:
            st.write("暂无数据")

with tab2:
    col_c, col_d = st.columns([1, 1])
    with col_c:
        fig_pie = px.pie(values=list(gameplay_counts.values()), names=list(gameplay_counts.keys()), title="玩法模式讨论占比")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_d:
        st.markdown("### 📝 热门原声")
        if gameplay_counts and max(gameplay_counts.values()) > 0:
            top_gameplay = max(gameplay_counts, key=gameplay_counts.get)
            st.caption(f"随机展示关于“{top_gameplay}”的评论：")
            
            # --- 🔴 修复点：先筛选，再计算长度，最后采样 ---
            target_reviews = df[df['Message'].str.contains(top_gameplay, na=False)]['Message']
            
            # 只有当有评论时才采样
            if len(target_reviews) > 0:
                # 采样数量不能超过实际拥有的评论数
                sample_size = min(3, len(target_reviews))
                sample_reviews = target_reviews.sample(sample_size).tolist()
                
                for review in sample_reviews:
                    st.text(f"“{review}”")
            else:
                st.text("该话题暂无详细评论。")
        else:
            st.text("暂无足够的热度数据。")

with tab3:
    st.metric("高风险反馈数", len(risk_df), delta_color="inverse")
    if not risk_df.empty:
        # --- 🔴 修复点：移除了 use_container_width 参数以消除警告（或者使用 width='stretch' 如果你的版本支持）---
        # 在较新版本的 Pandas Styler 或 Streamlit 中，默认行为通常已足够，
        # 如果需要全宽，st.dataframe(..., use_container_width=True) 在最新版是合法的，
        # 但根据你的报错，我们先去掉它，改由 layout="wide" 控制
        st.dataframe(risk_df[['Time', 'User', 'Message']], height=300) 
    else:
        st.success("暂无高风险内容")

# --- 4. 智能对话模块 (AI Controller) ---
st.markdown("---")
st.subheader("💬 AI 分析师 (GLM-4)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("问我任何问题..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    context_str = engine.generate_context_summary(df, item_counts, risk_df)
    
    system_prompt = f"""
    你是一个游戏数据分析师。请基于以下数据摘要回答用户问题：
    {context_str}
    如果用户问及具体细节，请根据常识和数据倾向进行专业回答。
    """
    
    api_msgs = [{"role": "system", "content": system_prompt}] + st.session_state.messages[-6:]
    
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            ai_reply = engine.call_ai_analysis(api_msgs)
            st.markdown(ai_reply)
            
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})