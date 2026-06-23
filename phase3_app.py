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

# ---------- 页面配置 ----------
st.set_page_config(page_title="校园搭子推荐系统", page_icon="🎓", layout="wide")

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
st.sidebar.title("🎓 校园搭子推荐系统")
st.sidebar.markdown("---")
st.sidebar.header("📋 你的消费画像")

food = st.sidebar.selectbox("每月餐饮伙食", [1, 2, 3, 4],
    format_func=lambda x: ['<600元', '600-900元', '901-1200元', '>1200元'][x-1])
social = st.sidebar.selectbox("每月社交娱乐", [1, 2, 3, 4],
    format_func=lambda x: ['<100元', '100-300元', '301-500元', '>500元'][x-1])
fashion = st.sidebar.selectbox("每月服饰美妆", [1, 2, 3, 4],
    format_func=lambda x: ['几乎不花', '100-300元', '301-500元', '>500元'][x-1])
study = st.sidebar.selectbox("每月学习发展", [1, 2, 3, 4],
    format_func=lambda x: ['几乎不花', '<50元', '50-150元', '>150元'][x-1])
digital = st.sidebar.selectbox("每月数码游戏", [1, 2, 3, 4],
    format_func=lambda x: ['几乎不花', '<100元', '100-300元', '>300元'][x-1])
budget = st.sidebar.selectbox("月生活费区间", [1, 2, 3, 4, 5],
    format_func=lambda x: ['≤1000', '1001-1500', '1501-2000', '2001-3000', '>3000'][x-1])
hobby = st.sidebar.selectbox("兴趣投入意愿", [1, 2, 3],
    format_func=lambda x: ['佛系不花', '偶尔小额', '高额投入'][x-1])

st.sidebar.markdown("---")
st.sidebar.header("🧠 快速 MBTI 自测（可选）")
st.sidebar.caption("跳过则仅用消费特征预测")

ei_answer = st.sidebar.radio("精力恢复方式",
    [None, 1, 2, 3],
    format_func=lambda x: '跳过' if x is None else ['独处静养(I)', '朋友聚会(E)', '两者皆可'][x-1])
sn_answer = st.sidebar.radio("信息处理方式",
    [None, 1, 2],
    format_func=lambda x: '跳过' if x is None else ['现实细节(S)', '未来灵感(N)'][x-1])
tf_answer = st.sidebar.radio("决策标准",
    [None, 1, 2],
    format_func=lambda x: '跳过' if x is None else ['客观逻辑(T)', '人情和谐(F)'][x-1])
jp_answer = st.sidebar.radio("生活风格",
    [None, 1, 2],
    format_func=lambda x: '跳过' if x is None else ['按部就班(J)', '随性灵活(P)'][x-1])

st.sidebar.markdown("---")
analyze_btn = st.sidebar.button("🔍 开始分析", type="primary", use_container_width=True)

# ---------- 主页面 ----------
st.title("🎓 基于MBTI与消费特征的校园搭子推荐系统")
st.markdown("> 输入你的消费习惯，系统将判断你的消费群体、预测MBTI性格，并推荐最匹配的校园搭子")

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
    tab1, tab2, tab3 = st.tabs(["📊 消费群体", "🧠 MBTI预测", "🤝 搭子推荐"])

    with tab1:
        cluster = kmeans.predict(user_consume_scaled)[0]
        st.subheader(f"你属于：**{CLUSTER_NAMES[cluster]}**")
        st.caption(f"基于 62 份真实校园问卷的 K-Means 聚类结果")

        # 雷达图：你的消费 vs 群体均值
        cluster_mean = df_full[df_full['cluster'] == cluster][feat_cols[:5]].mean().values
        categories = ['餐饮伙食', '社交娱乐', '服饰美妆', '学习发展', '数码游戏']

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=user_consume[0][:5].tolist() + [user_consume[0][0]],
            theta=categories + [categories[0]],
            fill='toself', name='你', line_color='#e74c3c',
        ))
        fig.add_trace(go.Scatterpolar(
            r=cluster_mean.tolist() + [cluster_mean[0]],
            theta=categories + [categories[0]],
            fill='toself', name=f'{CLUSTER_NAMES[cluster]}均值',
            line_color='#3498db',
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 4.5])),
                          height=450, margin=dict(t=40))
        st.plotly_chart(fig, use_container_width=True)

    # ----- Tab 2: MBTI预测 -----
    with tab2:
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
        cols = st.columns(4)
        for i, (dim_display, dim_key, lmap) in enumerate(zip(dim_names_display, dim_keys, label_maps)):
            user_full_scaled = rf_scalers[dim_key].transform(user_full)
            pred = rf_models[dim_key].predict(user_full_scaled)[0]
            predicted_mbti += lmap[pred][0]  # 取首字母I/E/X/S/N/T/F/J/P

            with cols[i]:
                st.metric(label=dim_display, value=lmap[pred])

        st.markdown("---")
        st.caption("⚠️ 以上预测基于 62 份样本训练的随机森林模型，准确率有限，仅供展示参考")

    # ----- Tab 3: 搭子推荐 -----
    with tab3:
        user_scene = st.selectbox("你偏好的结伴场景", [1, 2, 3, 4],
            format_func=lambda x: ['图书馆+简餐', '美食探店', '户外运动', '游戏/展演'][x-1],
            key='scene_selector')

        recs = recommend_matches(user_consume[0], predicted_mbti, user_scene, top_k=5)

        st.subheader("🎯 TOP-5 推荐搭子")

        scene_labels = {1: '图书馆+简餐', 2: '美食探店', 3: '户外运动', 4: '游戏/展演'}
        for rank, (idx, total, sim, bud, comp, scene) in enumerate(recs):
            row = df_full.iloc[idx]
            with st.container():
                cols = st.columns([1, 3, 1])
                with cols[0]:
                    st.markdown(f"### #{rank+1}")
                    st.metric("匹配度", f"{total:.0%}")
                with cols[1]:
                    st.markdown(f"**MBTI**: {row['mbti_str']}　|　**消费群体**: {CLUSTER_NAMES.get(row['cluster'], '?')}")
                    st.markdown(f"偏好场景: {scene_labels.get(row['scene_pref'], '?')}")
                    st.progress(total, text=f"消费相似度{sim:.2f} | 预算{bud:.2f} | 互补{comp:.2f} | 场景{scene:.2f}")
                with cols[2]:
                    st.caption(f"月预算档位: {int(row['monthly_budget'])}")
                    st.caption(f"餐饮: {int(row['consume_food'])} | 社交: {int(row['consume_social'])}")
                    st.caption(f"服饰: {int(row['consume_fashion'])} | 学习: {int(row['consume_study'])}")
                st.markdown("---")

else:
    st.info("👈 在左侧填写你的消费画像，然后点击「开始分析」")

# ---------- 页脚 ----------
st.markdown("---")
st.caption("基于 MBTI 心理特质与微观消费特征的校园圈层聚类与推荐系统 · 机器学习课程大作业")