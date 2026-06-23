"""
校园搭子推荐系统 - Flask 后端
启动方式：D:\ANACONDA\envs\ML_Course\python.exe app.py
"""
import pickle
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

# ========== 加载模型 ==========
print('[启动] 加载模型中...')

kmeans = pickle.load(open('model_kmeans.pkl', 'rb'))
scaler_cluster = pickle.load(open('model_scaler.pkl', 'rb'))
feat_cols_7 = pickle.load(open('model_feature_cols.pkl', 'rb'))
feat_cols_12 = pickle.load(open('model_feature_cols_phase2.pkl', 'rb'))

rf_models = {}
rf_scalers = {}
for dim in ['E_I_精力恢复', 'S_N_信息处理', 'T_F_决策标准', 'J_P_生活风格']:
    rf_models[dim] = pickle.load(open(f'model_rf_{dim}.pkl', 'rb'))
    rf_scalers[dim] = pickle.load(open(f'model_scaler_{dim}.pkl', 'rb'))

df_full = pd.read_csv('data_cleaned.csv')

CLUSTER_NAMES = {
    0: '高消费数码型',
    1: '节俭生存型',
    2: '社交体验型',
    3: '自我提升型',
}

CLUSTER_COLORS = {
    0: '#FF6B8A',
    1: '#4ECDC4',
    2: '#FFD93D',
    3: '#6C5CE7',
}

CLUSTER_DESC = {
    0: '预算充裕，热爱数码与游戏，兴趣投入高，是校园里的"装备党"和游戏达人。',
    1: '精打细算的务实派，各项消费节制，偏好高性价比的生活方式。',
    2: '社交达人，热衷聚餐和娱乐活动，注重外在形象，享受和朋友在一起的时光。',
    3: '注重自我成长，在学习发展和兴趣培养上投入最多，是校园里的"充电型"选手。',
}

print('[启动] 所有模型加载完成！')


def predict_mbti_features(user_full_vec):
    """用12维特征预测MBTI四维"""
    dim_keys = ['E_I_精力恢复', 'S_N_信息处理', 'T_F_决策标准', 'J_P_生活风格']
    label_maps = [
        {1: 'I(内倾)', 2: 'E(外倾)', 3: 'X(两者皆可)'},
        {1: 'S(感觉)', 2: 'N(直觉)'},
        {1: 'T(思考)', 2: 'F(情感)'},
        {1: 'J(判断)', 2: 'P(感知)'},
    ]
    results = {}
    mbti_str = ''
    for dim_key, lmap in zip(dim_keys, label_maps):
        X_scaled = rf_scalers[dim_key].transform(user_full_vec)
        pred = rf_models[dim_key].predict(X_scaled)[0]
        results[dim_key] = lmap[pred]
        mbti_str += lmap[pred][0]
    return results, mbti_str


def recommend_matches(user_vec_7, user_mbti_str, user_scene, top_k=5):
    """综合推荐搭子"""
    mbti_complement = [
        ('ENFP', 'INTJ'), ('ENTP', 'INFJ'), ('ESFP', 'ISTJ'), ('ESTP', 'ISFJ'),
        ('ENFJ', 'INTP'), ('ENTJ', 'INFP'), ('ESFJ', 'ISTP'), ('ESTJ', 'ISFP'),
    ]
    scores = []
    for idx, row in df_full.iterrows():
        target_vec = row[feat_cols_7].values.astype(float)
        cos_sim = cosine_similarity([user_vec_7], [target_vec])[0][0]
        sim_score = (cos_sim + 1) / 2
        budget_diff = abs(user_vec_7[5] - target_vec[5])
        budget_score = 1.0 if budget_diff <= 1 else 0.5 if budget_diff <= 2 else 0.0
        target_mbti = row['mbti_str']
        comp = 0.3
        for a, b in mbti_complement:
            if (user_mbti_str.startswith(a[:2]) and target_mbti.startswith(b[:2])) or \
               (user_mbti_str.startswith(b[:2]) and target_mbti.startswith(a[:2])):
                comp = 1.0
                break
        scene_score = 1.0 if user_scene == row['scene_pref'] else 0.0
        total = 0.40 * sim_score + 0.20 * budget_score + 0.20 * comp + 0.20 * scene_score
        scores.append({
            'index': int(idx),
            'total': round(total, 4),
            'sim': round(sim_score, 4),
            'budget': round(budget_score, 4),
            'complement': round(comp, 4),
            'scene': round(scene_score, 4),
            'mbti': row['mbti_str'],
            'cluster': int(row['cluster']),
            'cluster_name': CLUSTER_NAMES.get(row['cluster'], '?'),
            'scene_pref': int(row['scene_pref']),
            'monthly_budget': int(row['monthly_budget']),
            'consume_food': int(row['consume_food']),
            'consume_social': int(row['consume_social']),
            'consume_fashion': int(row['consume_fashion']),
            'consume_study': int(row['consume_study']),
        })
    scores.sort(key=lambda x: x['total'], reverse=True)
    return scores[:top_k]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供JSON数据'}), 400

    user_consume_7 = np.array([[
        data['food'], data['social'], data['fashion'],
        data['study'], data['digital'], data['budget'], data['hobby']
    ]])

    defaults = df_full[feat_cols_12].mode().iloc[0].values.astype(float)
    user_full_12 = np.array([[
        data['food'], data['social'], data['fashion'],
        data['study'], data['digital'], data['budget'],
        data['hobby'], defaults[7], defaults[8],
        defaults[9], defaults[10], defaults[11],
    ]])

    user_scaled = scaler_cluster.transform(user_consume_7)
    cluster_id = int(kmeans.predict(user_scaled)[0])

    cluster_mask = df_full['cluster'] == cluster_id
    cluster_mean = df_full[cluster_mask][feat_cols_7[:5]].mean().values.tolist()
    cluster_size = int(cluster_mask.sum())

    mbti_pred, mbti_str = predict_mbti_features(user_full_12)

    scene = data.get('scene', 1)
    matches = recommend_matches(user_consume_7[0], mbti_str, scene, top_k=5)

    return jsonify({
        'cluster': {
            'id': cluster_id,
            'name': CLUSTER_NAMES[cluster_id],
            'color': CLUSTER_COLORS[cluster_id],
            'description': CLUSTER_DESC[cluster_id],
            'size': cluster_size,
            'mean': cluster_mean,
        },
        'mbti': mbti_pred,
        'mbti_str': mbti_str,
        'user_consume': user_consume_7[0].tolist(),
        'matches': matches,
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
