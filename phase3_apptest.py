"""
阶段三：校园搭子推荐系统 Web 展示
启动方式：streamlit run phase3_app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# ---------- 页面配置 & 自定义样式 ----------
st.set_page_config(
    page_title="校园搭子推荐系统",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS：清新简约风格
st.markdown("""
    <style>
    /* 全局样式 */
    :root {
        --primary-color: #4B9CD3;
        --secondary-color: #95C8D8;
        --accent-color: #66C2A5;
        --light-bg: #F8FAFC;
        --card-bg: #FFFFFF;
        --text-color: #2D3748;
        --subtext-color: #718096;
    }
    
    body {
        background-color: var(--light-bg);
        color: var(--text-color);
        font-family: "Inter", "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    
    /* 侧边栏美化 */
    [data-testid="stSidebar"] {
        background-color: var(--card-bg);
        box-shadow: 0 0 20px rgba(0,0,0,0.05);
    }
    [data-testid="stSidebar"] .sidebar-content {
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: var(--primary-color);
        font-weight: 600;
    }
    [data-testid="stSidebar"] .stButton>button {
        background-color: var(--primary-color);
        border: none;
        border-radius: 8px;
        padding: 0.6rem 0;
        color: white;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #3A88C1;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(75, 156, 211, 0.3);
    }
    
    /* 主内容区美化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: var(--light-bg);
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* 卡片容器美化 */
    .stContainer {
        background-color: var(--card-bg);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 15px rgba(0,0,0,0.03);
        margin-bottom: 1rem;
    }
    
    /* 指标卡片美化 */
    [data-testid="stMetric"] {
        background-color: var(--card-bg);
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricLabel"] {
        color: var(--subtext-color);
        font-weight: 500;
    }
    [data-testid="stMetricValue"] {
        color: var(--primary-color);
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    /* 进度条美化 */
    [data-testid="stProgress"] > div > div {
        background-color: var(--accent-color);
        border-radius: 8px;
    }
    
    /* 按钮和选择框美化 */
    .stSelectbox [data-baseweb="select"] {
        border-radius: 8px;
        border: 1px solid #E2E8F0;
    }
    .stRadio [data-baseweb="radio"] {
        padding: 0.5rem 0;
    }
    
    /* 标题和文本美化 */
    h1, h2, h3, h4 {
        color: var(--primary-color);
        font-weight: 600;
    }
    .caption {
        color: var(--subtext-color) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------- 加载预训练模型与数据 ----------
@st.cache_resource
def load_models():
    kmeans = pickle.load(open('model_kmeans.pkl', 'rb'))
    scaler_cluster = pickle.load(open('model_scaler.pkl', 'rb'))
    feat_cols = pickle.load(open('model_feature_cols.pkl', 'rb'))
    feat_cols_12 = pickle.load(open('model_feature_cols_phase2.pkl', 'rb'))

    rf_models = {}
    rf_scalers = {}
    for dim in ['E_I_精力恢复', 'S_N_信息处理', 'T_F_决策标准', 'J_P_生活风格']:
        rf_models[dim] = pickle.load(open(f'model_rf_{dim}.pkl', 'rb'))
        rf_scalers[dim] = pickle.load(open(f'model_scaler_{dim}.pkl', 'rb'))

    return kmeans, scaler_cluster, feat_cols, feat_cols_12, rf_models, rf_scalers

@st.cache_data
def load_data():
    df = pd.read_csv('data_cleaned.csv')
    return df

kmeans, scaler_cluster, feat_cols, feat_cols_12, rf_models, rf_scalers = load_models()
df_full = load_data()

# ---------- 群体命名 ----------
CLUSTER_NAMES = {
    0: "高消费数码型",
    1: "节俭生存型",
    2: "社交体验型",
    3: "自我提升型",
}

# ---------- 推荐函数 ----------
def recommend_matches(user_vec, user_mbti, user_scene, top_k=5):
    """
    user_vec: 7维消费向量（与FEATURE_COLS一致）
    """
    scores = []
    for idx, row in df_full.iterrows():
        target_vec = row[feat_cols].values.astype(float)

        # 1. 消费相似度（余弦）
        cos_sim = cosine_similarity([user_vec], [target_vec])[0][0]
        sim_score = (cos_sim + 1) / 2  # 归一化到 [0, 1]

        # 2. 预算匹配
        budget_diff = abs(user_vec[5] - target_vec[5])  # monthly_budget是第6个
        budget_score = 1.0 if budget_diff <= 1 else 0.5 if budget_diff <= 2 else 0.0

        # 3. MBTI互补加分（经典配对）
        mbti_complement_pairs = [
            ('ENFP', 'INTJ'), ('ENTP', 'INFJ'), ('ESFP', 'ISTJ'), ('ESTP', 'ISFJ'),
            ('ENFJ', 'INTP'), ('ENTJ', 'INFP'), ('ESFJ', 'ISTP'), ('ESTJ', 'ISFP'),
        ]
        target_mbti = row['mbti_str']
        complement = 0.3
        for a, b in mbti_complement_pairs:
            if (user_mbti.startswith(a[:2]) and target_mbti.startswith(b[:2])) or \
               (user_mbti.startswith(b[:2]) and target_mbti.startswith(a[:2])):
                complement = 1.0
                break

        # 4. 场景偏好一致
        scene_score = 1.0 if user_scene == row['scene_pref'] else 0.0

        total = 0.40 * sim_score + 0.20 * budget_score + 0.20 * complement + 0.20 * scene_score
        scores.append((idx, total, sim_score, budget_score, complement, scene_score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]

# ---------- 侧边栏：用户输入 ----------
with st.sidebar:
    st.markdown("<h2 style='text-align: center; margin-bottom: 1rem;'>🎓 校园搭子推荐</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # 消费画像模块
    st.markdown("<h3 style='margin-bottom: 0.8rem;'>📋 你的消费画像</h3>", unsafe_allow_html=True)
    st.markdown("<div style='background-color: #F1F5F9; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>", unsafe_allow_html=True)
    food = st.selectbox("🍚 每月餐饮伙食", [1, 2, 3, 4],
        format_func=lambda x: ['<600元', '600-900元', '901-1200元', '>1200元'][x-1],
        key="food")
    social = st.selectbox("🎮 每月社交娱乐", [1, 2, 3, 4],
        format_func=lambda x: ['<100元', '100-300元', '301-500元', '>500元'][x-1],
        key="social")
    fashion = st.selectbox("👗 每月服饰美妆", [1, 2, 3, 4],
        format_func=lambda x: ['几乎不花', '100-300元', '301-500元', '>500元'][x-1],
        key="fashion")
    study = st.selectbox("📚 每月学习发展", [1, 2, 3, 4],
        format_func=lambda x: ['几乎不花', '<50元', '50-150元', '>150元'][x-1],
        key="study")
    digital = st.selectbox("💻 每月数码游戏", [1, 2, 3, 4],
        format_func=lambda x: ['几乎不花', '<100元', '100-300元', '>300元'][x-1],
        key="digital")
    budget = st.selectbox("💰 月生活费区间", [1, 2, 3, 4, 5],
        format_func=lambda x: ['≤1000', '1001-1500', '1501-2000', '2001-3000', '>3000'][x-1],
        key="budget")
    hobby = st.selectbox("🌟 兴趣投入意愿", [1, 2, 3],
        format_func=lambda x: ['佛系不花', '偶尔小额', '高额投入'][x-1],
        key="hobby")
    st.markdown("</div>", unsafe_allow_html=True)

    # MBTI自测模块
    st.markdown("---")
    st.markdown("<h3 style='margin-bottom: 0.8rem;'>🧠 快速 MBTI 自测</h3>", unsafe_allow_html=True)
    st.caption("（跳过则仅用消费特征预测）")
    st.markdown("<div style='background-color: #F1F5F9; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>", unsafe_allow_html=True)
    ei_answer = st.radio("🔋 精力恢复方式",
        [None, 1, 2, 3],
        format_func=lambda x: '跳过' if x is None else ['独处静养(I)', '朋友聚会(E)', '两者皆可'][x-1],
        key="ei")
    sn_answer = st.radio("📥 信息处理方式",
        [None, 1, 2],
        format_func=lambda x: '跳过' if x is None else ['现实细节(S)', '未来灵感(N)'][x-1],
        key="sn")
    tf_answer = st.radio("⚖️ 决策标准",
        [None, 1, 2],
        format_func=lambda x: '跳过' if x is None else ['客观逻辑(T)', '人情和谐(F)'][x-1],
        key="tf")
    jp_answer = st.radio("🗓️ 生活风格",
        [None, 1, 2],
        format_func=lambda x: '跳过' if x is None else ['按部就班(J)', '随性灵活(P)'][x-1],
        key="jp")
    st.markdown("</div>", unsafe_allow_html=True)

    # 分析按钮
    st.markdown("---")
    analyze_btn = st.button("🔍 开始分析", type="primary", use_container_width=True)

# ---------- 主页面 ----------
st.markdown("<h1 style='text-align: center; margin-bottom: 1rem;'>🎓 校园搭子推荐系统</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: var(--subtext-color); margin-bottom: 2rem;'>基于MBTI与消费特征，找到最合拍的校园搭子</p>", unsafe_allow_html=True)

if analyze_btn:
    # ----- 构建用户特征向量（仅用7维消费特征做聚类）-----
    user_consume = np.array([[food, social, fashion, study, digital, budget, hobby]])
    user_consume_scaled = scaler_cluster.transform(user_consume)

    # 补全12维（用均值填充人口学特征，因为用户不会填性别年级）
    user_full = np.zeros((1, 12))
    user_full[0, :7] = user_consume[0]
    # 人口学特征用数据集的众数填充
    for i in range(7, 12):
        user_full[0, i] = df_full.iloc[:, df_full.columns.get_loc(feat_cols_12[i])].mode()[0]

    # ----- Tab 1: 聚类结果 -----
    tab1, tab2, tab3 = st.tabs(["📊 消费群体分析", "🧠 MBTI性格预测", "🤝 最佳搭子推荐"])

    with tab1:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        cluster = kmeans.predict(user_consume_scaled)[0]
        st.markdown(f"<h3 style='text-align: center;'>你的消费标签：<span style='color: var(--accent-color);'>{CLUSTER_NAMES[cluster]}</span></h3>", unsafe_allow_html=True)
        st.caption(f"基于 62 份真实校园问卷的 K-Means 聚类结果 | 消费特征匹配度分析")
        st.markdown("---")

        # 雷达图：你的消费 vs 群体均值（清新配色）
        cluster_mean = df_full[df_full['cluster'] == cluster][feat_cols[:5]].mean().values
        categories = ['餐饮伙食', '社交娱乐', '服饰美妆', '学习发展', '数码游戏']

        fig = go.Figure()
        # 个人消费曲线（清新粉蓝）
        fig.add_trace(go.Scatterpolar(
            r=user_consume[0][:5].tolist() + [user_consume[0][0]],
            theta=categories + [categories[0]],
            fill='toself',
            name='你的消费特征',
            line_color='#66C2A5',
            fillcolor='rgba(102, 194, 165, 0.2)',
        ))
        # 群体均值曲线（柔和蓝）
        fig.add_trace(go.Scatterpolar(
            r=cluster_mean.tolist() + [cluster_mean[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name=f'{CLUSTER_NAMES[cluster]}均值',
            line_color='#4B9CD3',
            fillcolor='rgba(75, 156, 211, 0.2)',
        ))
        # 图表样式优化
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 4.5], tickfont=dict(color='#718096')),
                angularaxis=dict(tickfont=dict(color='#2D3748', size=12))
            ),
            height=500,
            margin=dict(t=40, b=20, l=20, r=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5,
                font=dict(color='#2D3748')
            )
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- Tab 2: MBTI预测 -----
    with tab2:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        # 用RF模型预测四个维度
        dim_names_display = ['E/I (精力恢复)', 'S/N (信息处理)', 'T/F (决策标准)', 'J/P (生活风格)']
        dim_keys = ['E_I_精力恢复', 'S_N_信息处理', 'T_F_决策标准', 'J_P_生活风格']
        label_maps = [
            {1: 'I(内倾)', 2: 'E(外倾)', 3: 'X(两者皆可)'},
            {1: 'S(感觉)', 2: 'N(直觉)'},
            {1: 'T(思考)', 2: 'F(情感)'},
            {1: 'J(判断)', 2: 'P(感知)'},
        ]

        predicted_mbti = ''
        cols = st.columns(4, gap="medium")
        for i, (dim_display, dim_key, lmap) in enumerate(zip(dim_names_display, dim_keys, label_maps)):
            user_full_scaled = rf_scalers[dim_key].transform(user_full)
            pred = rf_models[dim_key].predict(user_full_scaled)[0]
            predicted_mbti += lmap[pred][0]  # 取首字母I/E/X/S/N/T/F/J/P

            with cols[i]:
                st.metric(label=dim_display, value=lmap[pred])

        st.markdown("---")
        st.markdown(f"<h4 style='text-align: center;'>综合预测 MBTI 类型：<span style='color: var(--accent-color);'>{predicted_mbti}</span></h4>", unsafe_allow_html=True)
        st.caption("⚠️ 预测基于 62 份样本训练的随机森林模型，仅供参考 | 真正的MBTI需专业测评")
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- Tab 3: 搭子推荐 -----
    with tab3:
        st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
        # 场景选择（美化）
        st.markdown("<h4 style='margin-bottom: 1rem;'>📍 选择你偏好的结伴场景</h4>", unsafe_allow_html=True)
        user_scene = st.selectbox("", [1, 2, 3, 4],
            format_func=lambda x: ['📖 图书馆+简餐', '🍜 美食探店', '🏃 户外运动', '🎮 游戏/展演'][x-1],
            key='scene_selector',
            label_visibility="collapsed")

        recs = recommend_matches(user_consume[0], predicted_mbti, user_scene, top_k=5)

        st.markdown("---")
        st.markdown("<h3 style='text-align: center; margin-bottom: 1.5rem;'>🎯 TOP-5 最佳匹配搭子</h3>", unsafe_allow_html=True)

        scene_labels = {1: '图书馆+简餐', 2: '美食探店', 3: '户外运动', 4: '游戏/展演'}
        for rank, (idx, total, sim, bud, comp, scene) in enumerate(recs):
            row = df_full.iloc[idx]
            # 搭子卡片美化
            st.markdown(f"""
                <div style='background-color: #F8FAFC; border-left: 4px solid var(--accent-color); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <h4 style='margin: 0; color: var(--primary-color);'>#{rank+1} 匹配搭子</h4>
                        <span style='background-color: var(--primary-color); color: white; padding: 0.2rem 0.8rem; border-radius: 20px; font-weight: 600;'>{total:.0%}</span>
                    </div>
                    <div style='display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 0.8rem;'>
                        <span>🧠 MBTI：{row['mbti_str']}</span>
                        <span>🏷️ 消费群体：{CLUSTER_NAMES.get(row['cluster'], '?')}</span>
                        <span>📍 偏好场景：{scene_labels.get(row['scene_pref'], '?')}</span>
                    </div>
                    <div style='font-size: 0.9rem; color: var(--subtext-color); margin-bottom: 0.5rem;'>
                        消费相似度 {sim:.2f} | 预算匹配 {bud:.2f} | MBTI互补 {comp:.2f} | 场景契合 {scene:.2f}
                    </div>
                    <div style='font-size: 0.85rem; color: var(--subtext-color);'>
                        💰 月预算档位：{int(row['monthly_budget'])} | 🍚 餐饮：{int(row['consume_food'])} | 🎮 社交：{int(row['consume_social'])} | 👗 服饰：{int(row['consume_fashion'])} | 📚 学习：{int(row['consume_study'])}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # 初始页面美化
    st.markdown("<div class='stContainer' style='text-align: center; padding: 3rem 2rem;'>", unsafe_allow_html=True)
    st.markdown("<h3>👈 填写左侧的消费画像与MBTI自测</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--subtext-color); margin-top: 1rem;'>完成后点击「开始分析」，即可获取专属消费标签、MBTI预测和最佳搭子推荐</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- 页脚 ----------
st.markdown("---")
st.markdown("<p style='text-align: center; color: var(--subtext-color); font-size: 0.9rem;'>基于 MBTI 心理特质与微观消费特征的校园圈层聚类与推荐系统 · 机器学习课程大作业</p>", unsafe_allow_html=True)