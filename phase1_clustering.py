"""
阶段一：数据清洗与无监督聚类
项目：基于MBTI心理特质与微观消费特征的校园圈层聚类与推荐系统
数据：69份有效问卷（截至当前）
注：第13题(E/I维度)含"两者皆可"选项，因此E/I为三分类，其余维度为二分类
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

# 支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. 加载数据
# ============================================================
DATA_FILE = 'MBTI性格与大学生消费行为关联.xlsx'
df_raw = pd.read_excel(DATA_FILE)
print(f'[加载] 原始数据: {df_raw.shape[0]} 行 × {df_raw.shape[1]} 列')

# ============================================================
# 2. 列名映射 — 方便后续引用
# ============================================================
COLUMN_MAP = {
    '序号':              'id',
    '提交答卷时间':        'submit_time',
    '所用时间':           'duration',
    '来源':              'source',
    '来源详情':           'source_detail',
    '来自IP':            'ip',
    '你的性别?':          'gender',
    '所在年级?':          'grade',
    '你的生活费主要来源是?': 'income_source',
    '你每月的总生活费大概在哪个区间?': 'monthly_budget',
    '5. 每月【餐饮伙食】（一日三餐、水果饮料）大概花费?': 'consume_food',
    '6. 每月【社交娱乐】（聚餐、看电影、剧本杀、旅游平摊等）大概花费?': 'consume_social',
    '7. 每月【服饰美妆】（买衣服鞋包、护肤化妆品等）大概花费?': 'consume_fashion',
    '8. 每月【学习发展】（买书、考证报名、知识付费等）大概花费?': 'consume_study',
    '9. 每月【数码与游戏】（充值游戏、购买电子外设等）大概花费?': 'consume_digital',
    '10. 你的日常消费决策习惯是?':            'decision_style',
    '11. 你的选购商品首要看重因素?':           'priority_factor',
    '12. 你对于兴趣爱好（如追星、摄影、手办、运动等）的投入意愿?': 'hobby_spend',
    '13. 经过一周的疲惫学习，你更倾向于哪种精力恢复方式?': 'mbti_ei',
    '14. 在接收和处理信息时，你更倾向于?':              'mbti_sn',
    '15. 在做决定时，你的评判标准通常是?':              'mbti_tf',
    '16. 你的日常行事与生活风格是?':                    'mbti_jp',
    '17. 你更偏好结交哪种消费观念的朋友?':               'friend_pref',
    '18. 如果校园内有一款基于性格和消费观的"搭子"推荐系统，你的态度是?': 'app_attitude',
    '19. 你最心仪的校园结伴消费场景是?':                 'scene_pref',
}
df = df_raw.rename(columns=COLUMN_MAP)

# ============================================================
# 3. 数值编码 → 标签映射字典
#    （基于问卷原文，供后续论文/图表引用）
# ============================================================
LABEL_MAP = {
    'gender':          {1: '男', 2: '女'},
    'grade':           {1: '大一', 2: '大二', 3: '大三', 4: '大四', 5: '研究生及以上'},
    'income_source':   {1: '全部父母提供', 2: '父母为主+兼职', 3: '兼职为主+独立'},
    'monthly_budget':  {1: '≤1000元', 2: '1001-1500元', 3: '1501-2000元',
                        4: '2001-3000元', 5: '>3000元'},
    'consume_food':    {1: '<600元', 2: '600-900元', 3: '901-1200元', 4: '>1200元'},
    'consume_social':  {1: '<100元', 2: '100-300元', 3: '301-500元', 4: '>500元'},
    'consume_fashion': {1: '几乎不花', 2: '100-300元', 3: '301-500元', 4: '>500元'},
    'consume_study':   {1: '几乎不花', 2: '<50元', 3: '50-150元', 4: '>150元'},
    'consume_digital': {1: '几乎不花', 2: '<100元', 3: '100-300元', 4: '>300元'},
    'decision_style':  {1: '计划预算', 2: '按需消费', 3: '易受安利', 4: '冲动消费'},
    'priority_factor': {1: '性价比实用', 2: '颜值喜好', 3: '品牌口碑'},
    'hobby_spend':     {1: '佛系不花', 2: '偶尔小额', 3: '高额投入'},
    'mbti_ei':         {1: 'I(内倾)', 2: 'E(外倾)', 3: 'X(两者皆可)'},
    'mbti_sn':         {1: 'S(感觉)', 2: 'N(直觉)'},
    'mbti_tf':         {1: 'T(思考)', 2: 'F(情感)'},
    'mbti_jp':         {1: 'J(判断)', 2: 'P(感知)'},
    'friend_pref':     {1: '节俭务实', 2: '注重体验', 3: '兴趣相投', 4: '极简主义'},
    'app_attitude':    {1: '非常感兴趣', 2: '稍有兴趣', 3: '不太感兴趣'},
    'scene_pref':      {1: '图书馆+简餐', 2: '美食探店', 3: '户外运动', 4: '游戏/展演'},
}

# ============================================================
# 4. 数据清洗
# ============================================================

# 4.1 解析填写时间（去掉"秒"字）
df['duration_sec'] = df['duration'].str.replace('秒', '', regex=False).astype(int)

# 4.2 脏数据检测规则
print('\n========== 数据清洗 ==========')

# 标记：填写时间过短（<30秒即乱填）
fast_mask = df['duration_sec'] < 30
print(f'[清洗] 填写时间 <30秒: {fast_mask.sum()} 人 (已标记)')

# 标记：所有消费维度答案完全相同（可能是"全部选A"的应付答卷）
consume_cols = ['consume_food', 'consume_social', 'consume_fashion',
                'consume_study', 'consume_digital']
all_same_mask = df[consume_cols].nunique(axis=1) == 1
print(f'[清洗] 五维消费答案完全相同: {all_same_mask.sum()} 人 (已标记)')

# 注：已移除"MBTI四维全同"规则。
# 审查发现全部11条被标记记录均为真实ISTJ类型（全选"1"），
# 其中真正乱填者（#9,#10,#38）已被"时长<30s"和"消费全同"两条规则兜底覆盖，
# 其余8人均为消费有差异、填写时长正常的有效样本。

# 合并脏数据标记
dirty_mask = fast_mask | all_same_mask
df['is_dirty'] = dirty_mask
df_clean = df[~dirty_mask].copy()
print(f'[清洗] 清洗前: {len(df)} 份 → 清洗后: {len(df_clean)} 份')
print(f'[清洗] 剔除: {dirty_mask.sum()} 份脏数据')

# ============================================================
# 5. 描述性统计预览
# ============================================================
print('\n========== 消费五维度分布 ==========')
for col in consume_cols:
    print(f'\n--- {col} ---')
    dist = df_clean[col].value_counts().sort_index()
    for k, v in dist.items():
        label = LABEL_MAP[col].get(k, str(k))
        print(f'  {label}: {v} 人 ({v/len(df_clean)*100:.1f}%)')

# MBTI 分布
print('\n========== MBTI 类型分布 ==========')
df_clean['mbti_str'] = (
    df_clean['mbti_ei'].map({1: 'I', 2: 'E', 3: 'X'}) +
    df_clean['mbti_sn'].map({1: 'S', 2: 'N'}) +
    df_clean['mbti_tf'].map({1: 'T', 2: 'F'}) +
    df_clean['mbti_jp'].map({1: 'J', 2: 'P'})
)
mbti_dist = df_clean['mbti_str'].value_counts()
print(mbti_dist.to_string())

# ============================================================
# 6. 聚类特征准备
# ============================================================
#   — 消费五维度（作为主要聚类输入）
#   — 每月总预算、消费决策风格、兴趣投入作为辅助
FEATURE_COLS = consume_cols + ['monthly_budget', 'hobby_spend']

X = df_clean[FEATURE_COLS].astype(float)

# 标准化
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f'\n[特征] 聚类特征: {FEATURE_COLS}')
print(f'[特征] 标准化后 shape: {X_scaled.shape}')

# ============================================================
# 7. 肘部法则 — 确定最优 K
# ============================================================
inertias = []
silhouettes = []
K_range = range(2, 9)

for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    inertias.append(km.inertia_)
    silhouettes.append(silhouette_score(X_scaled, labels))

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].plot(K_range, inertias, 'bo-')
axes[0].set_xlabel('K (聚类数)')
axes[0].set_ylabel('Inertia (簇内平方和)')
axes[0].set_title('肘部法则 — Elbow Method')
axes[0].grid(True, alpha=0.3)

axes[1].plot(K_range, silhouettes, 'ro-')
axes[1].set_xlabel('K (聚类数)')
axes[1].set_ylabel('Silhouette Score')
axes[1].set_title('轮廓系数 — Silhouette Score')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('output_elbow_silhouette.png', dpi=150, bbox_inches='tight')
plt.close()
print('\n[图表] 肘部法则图已保存: output_elbow_silhouette.png')

# ============================================================
# 8. 执行 K-Means 聚类（此处以 K=4 为例，可根据肘部图调整）
# ============================================================
OPTIMAL_K = 4  # ← 运行后根据肘部图手动调整
kmeans = KMeans(n_clusters=OPTIMAL_K, random_state=42, n_init=10)
df_clean['cluster'] = kmeans.fit_predict(X_scaled)

print(f'\n========== K-Means 聚类结果 (K={OPTIMAL_K}) ==========')
cluster_sizes = df_clean['cluster'].value_counts().sort_index()
for c in range(OPTIMAL_K):
    print(f'  群体 {c}: {cluster_sizes.get(c, 0)} 人')

# ============================================================
# 9. 聚类画像 — 每个群体的消费特征均值
# ============================================================
cluster_profile = df_clean.groupby('cluster')[FEATURE_COLS].mean()
# 用原始数值（非标准化）展示，便于理解
# 同时附加可读标签
print('\n========== 各群体消费特征均值（原始数值） ==========')
print(cluster_profile.round(2).to_string())

# 用标签解读
print('\n========== 群体画像解读 ==========')
for c in range(OPTIMAL_K):
    row = cluster_profile.loc[c]
    food = row['consume_food']
    social = row['consume_social']
    fashion = row['consume_fashion']
    study = row['consume_study']
    digital = row['consume_digital']
    budget = row['monthly_budget']
    hobby = row['hobby_spend']

    # 简单启发式命名
    traits = []
    if social >= 3.0:
        traits.append('社交活跃')
    if fashion >= 2.5:
        traits.append('注重外表')
    if study >= 2.5:
        traits.append('学习投入')
    if digital >= 2.5:
        traits.append('数码玩家')
    if food < 2.0:
        traits.append('低餐饮开销')
    if budget <= 2.0:
        traits.append('预算紧张')
    elif budget >= 4.0:
        traits.append('高预算群体')

    name = ' + '.join(traits) if traits else '均衡型'
    print(f'  群体 {c} (n={cluster_sizes[c]}): {name}')
    print(f'    餐饮{food:.1f} | 社交{social:.1f} | 服饰{fashion:.1f} | 学习{study:.1f} | 数码{digital:.1f} | 月预算{budget:.1f}')

# ============================================================
# 10. 可视化 — 雷达图（群体对比）
# ============================================================
def plot_radar():
    """绘制各消费群体的雷达图"""
    categories = ['餐饮伙食', '社交娱乐', '服饰美妆', '学习发展', '数码游戏']
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # 闭合

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
    for c in range(OPTIMAL_K):
        values = cluster_profile.loc[c, consume_cols].values.tolist()
        values += values[:1]
        ax.fill(angles, values, alpha=0.1, color=colors[c])
        ax.plot(angles, values, 'o-', linewidth=2, color=colors[c],
                label=f'群体{c} (n={cluster_sizes[c]})')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylim(0, 4.5)
    ax.set_title(f'消费群体雷达图 (K={OPTIMAL_K})', fontsize=14, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    plt.tight_layout()
    plt.savefig('output_radar.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('[图表] 雷达图已保存: output_radar.png')

plot_radar()

# ============================================================
# 11. 可视化 — 消费特征热力图
# ============================================================
def plot_heatmap():
    """绘制群体 × 消费特征的热力图"""
    heat_data = cluster_profile.copy()
    # 用标签重命名列
    heat_data.columns = ['餐饮', '社交', '服饰', '学习', '数码', '月预算', '兴趣投入']
    heat_data.index = [f'群体{c}' for c in heat_data.index]

    fig, ax = plt.subplots(figsize=(9, 4))
    sns.heatmap(heat_data, annot=True, fmt='.2f', cmap='YlOrRd',
                linewidths=1, linecolor='white', ax=ax,
                vmin=1, vmax=4, cbar_kws={'label': '消费等级均值'})
    ax.set_title(f'消费群体热力图 — 各特征均值对比 (K={OPTIMAL_K})', fontsize=13, pad=12)
    plt.tight_layout()
    plt.savefig('output_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('[图表] 热力图已保存: output_heatmap.png')

plot_heatmap()

# ============================================================
# 12. 可视化 — PCA 降维散点图（2D 投影查看聚类分布）
# ============================================================
def plot_pca():
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
    for c in range(OPTIMAL_K):
        mask = df_clean['cluster'] == c
        ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
                   c=colors[c], label=f'群体{c} (n={mask.sum()})',
                   alpha=0.7, edgecolors='white', linewidth=0.5, s=80)

    # 标注聚类中心
    centers_pca = pca.transform(kmeans.cluster_centers_)
    ax.scatter(centers_pca[:, 0], centers_pca[:, 1],
               c='black', marker='X', s=200, linewidths=2, label='聚类中心')

    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} 方差)')
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} 方差)')
    ax.set_title(f'PCA 聚类分布 (K={OPTIMAL_K})', fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('output_pca.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('[图表] PCA散点图已保存: output_pca.png')

plot_pca()

# ============================================================
# 13. 导出清洗后的数据
# ============================================================
df_clean.to_csv('data_cleaned.csv', index=False, encoding='utf-8-sig')
print('\n[导出] 清洗后数据已保存: data_cleaned.csv')

# ============================================================
# 14. 聚类结果摘要
# ============================================================
summary = df_clean.groupby('cluster').agg(
    人数=('cluster', 'count'),
    月均预算=('monthly_budget', 'mean'),
    餐饮均值=('consume_food', 'mean'),
    社交均值=('consume_social', 'mean'),
    服饰均值=('consume_fashion', 'mean'),
    学习均值=('consume_study', 'mean'),
    数码均值=('consume_digital', 'mean'),
    兴趣投入=('hobby_spend', 'mean'),
    主流MBTI=('mbti_str', lambda x: x.mode().iloc[0] if not x.mode().empty else '-'),
).round(2)

summary.to_csv('cluster_summary.csv', encoding='utf-8-sig')
print('[导出] 聚类摘要已保存: cluster_summary.csv')
print('\n' + '='*60)
print(summary.to_string())
print('='*60)

# 保存模型供阶段三使用
import pickle
with open('model_kmeans.pkl', 'wb') as f:
    pickle.dump(kmeans, f)
with open('model_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
pickle.dump(FEATURE_COLS, open('model_feature_cols.pkl', 'wb'))
print('[导出] 模型文件已保存: model_kmeans.pkl, model_scaler.pkl, model_feature_cols.pkl')

print('\n✅ 阶段一脚本执行完毕！')
print('   生成文件:')
print('     output_elbow_silhouette.png — 肘部法则+轮廓系数')
print('     output_radar.png            — 群体消费雷达图')
print('     output_heatmap.png          — 群体特征热力图')
print('     output_pca.png              — PCA聚类分布散点图')
print('     data_cleaned.csv            — 清洗后数据集')
print('     cluster_summary.csv         — 聚类结果汇总表')
