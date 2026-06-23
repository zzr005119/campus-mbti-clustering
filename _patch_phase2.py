import os

new_file = r"D:\Xx\大二下\机器学习\大作业\phase2_mbti_classifier.py"

content = '''"""
阶段二：MBTI性格预测模型 (v2 — 增强评估指标)
项目：基于MBTI心理特质与微观消费特征的校园圈层聚类与推荐系统
目标：用消费特征(X)预测MBTI四个维度(Y)

新增指标:
  - F1-score (macro + per-class)
  - AUC-ROC (二分类 dims) / macro AUC (E/I 三分类)
  - Precision / Recall per class
  - 95% Bootstrap 置信区间 (Acc, F1, AUC)
  - Dummy Classifier 基线对比
  - ROC 曲线图
  - 指标对比柱状图
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.metrics import (accuracy_score, confusion_matrix,
                              classification_report, ConfusionMatrixDisplay,
                              f1_score, precision_score, recall_score,
                              roc_auc_score, roc_curve, auc)
from sklearn.model_selection import LeaveOneOut
from sklearn.dummy import DummyClassifier
from imblearn.over_sampling import SMOTENC

warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 0. 加载数据
# ============================================================
df = pd.read_csv('data_cleaned.csv')
print(f'[加载] data_cleaned.csv: {len(df)} 条记录')

# ============================================================
# 1. 特征工程
# ============================================================
CONSUME_COLS = ['consume_food', 'consume_social', 'consume_fashion',
                'consume_study', 'consume_digital']
AUX_COLS = ['monthly_budget', 'hobby_spend', 'decision_style', 'priority_factor']
DEMO_COLS = ['gender', 'grade', 'income_source']
FEATURE_COLS = CONSUME_COLS + AUX_COLS + DEMO_COLS
X_all = df[FEATURE_COLS].astype(float)

CATEGORICAL_INDICES = [
    FEATURE_COLS.index('decision_style'),
    FEATURE_COLS.index('priority_factor'),
    FEATURE_COLS.index('gender'),
    FEATURE_COLS.index('income_source'),
]

print(f'[特征] 总计 {len(FEATURE_COLS)} 维')

# ============================================================
# 2. Bootstrap CI 工具函数
# ============================================================
def bootstrap_ci(metric_fn, y_true, y_pred, n_bootstrap=2000, alpha=0.05, **kwargs):
    n = len(y_true)
    scores = []
    rng = np.random.RandomState(42)
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n, n)
        s = metric_fn(y_true[idx], y_pred[idx], **kwargs)
        scores.append(s)
    return np.percentile(scores, 100*alpha/2), np.percentile(scores, 100*(1-alpha/2))

def bootstrap_ci_auc(y_true_bin, y_proba, n_bootstrap=2000, alpha=0.05):
    n = len(y_true_bin)
    scores = []
    rng = np.random.RandomState(42)
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n, n)
        try:
            s = roc_auc_score(y_true_bin[idx], y_proba[idx])
        except ValueError:
            s = 0.5
        scores.append(s)
    return np.percentile(scores, 100*alpha/2), np.percentile(scores, 100*(1-alpha/2))

# ============================================================
# 3. 目标变量定义
# ============================================================
TARGETS = {
    'E/I (精力恢复)': {
        'col': 'mbti_ei',
        'labels': {1: 'I', 2: 'E', 3: 'X'},
        'n_classes': 3,
    },
    'S/N (信息处理)': {
        'col': 'mbti_sn',
        'labels': {1: 'S', 2: 'N'},
        'n_classes': 2,
    },
    'T/F (决策标准)': {
        'col': 'mbti_tf',
        'labels': {1: 'T', 2: 'F'},
        'n_classes': 2,
    },
    'J/P (生活风格)': {
        'col': 'mbti_jp',
        'labels': {1: 'J', 2: 'P'},
        'n_classes': 2,
    },
}

# ============================================================
# 4. LOOCV + SMOTENC 训练与逐维度评估
# ============================================================
results = {}
all_feature_importances = {}

for dim_name, tinfo in TARGETS.items():
    col = tinfo['col']
    y = df[col].values
    n_classes = tinfo['n_classes']
    labels_dict = tinfo['labels']

    class_counts = pd.Series(y).value_counts().sort_index()
    print(f'\\n{\"=\"*60}')
    print(f'维度: {dim_name}  ({n_classes}分类)')
    print(f'{\"=\"*60}')
    for k, v in class_counts.items():
        print(f'  {labels_dict.get(k, k)}: {v} 人 ({v/len(y)*100:.1f}%)')

    # --- LOOCV ---
    loo = LeaveOneOut()
    y_true_all, y_pred_all, y_proba_all = [], [], []

    for train_idx, test_idx in loo.split(X_all):
        X_train_raw = X_all.iloc[train_idx].values
        y_train = y[train_idx]
        X_test_raw = X_all.iloc[test_idx].values
        y_test = y[test_idx]

        min_class_count = np.min(np.bincount(y_train))
        smote_k = min(3, max(1, min_class_count - 1))
        try:
            if smote_k >= 1 and min_class_count > 1:
                smote = SMOTENC(categorical_features=CATEGORICAL_INDICES,
                                k_neighbors=smote_k, random_state=42)
                X_train, y_train = smote.fit_resample(X_train_raw, y_train)
            else:
                X_train, y_train = X_train_raw, y_train
        except Exception:
            X_train, y_train = X_train_raw, y_train

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test_raw)

        rf = RandomForestClassifier(n_estimators=100, max_depth=5,
                                     min_samples_leaf=3, class_weight='balanced',
                                     random_state=42)
        rf.fit(X_train_s, y_train)
        y_pred = rf.predict(X_test_s)
        y_proba = rf.predict_proba(X_test_s)[0]

        y_true_all.append(y_test[0])
        y_pred_all.append(y_pred[0])
        y_proba_all.append(y_proba)

    y_true_all = np.array(y_true_all)
    y_pred_all = np.array(y_pred_all)
    y_proba_all = np.array(y_proba_all)

    # --- 计算指标 ---
    acc = accuracy_score(y_true_all, y_pred_all)
    f1_m = f1_score(y_true_all, y_pred_all, average='macro', zero_division=0)
    prec_m = precision_score(y_true_all, y_pred_all, average='macro', zero_division=0)
    rec_m = recall_score(y_true_all, y_pred_all, average='macro', zero_division=0)

    # AUC
    if n_classes == 2:
        auc_v = roc_auc_score(y_true_all, y_proba_all[:, 1])
        auc_lo, auc_hi = bootstrap_ci_auc((y_true_all == 2).astype(int), y_proba_all[:, 1])
    else:
        y_bin = label_binarize(y_true_all, classes=sorted(np.unique(y)))
        try:
            auc_v = roc_auc_score(y_bin, y_proba_all, average='macro', multi_class='ovr')
        except ValueError:
            auc_v = np.nan
        auc_lo, auc_hi = np.nan, np.nan

    # Bootstrap CIs
    acc_lo, acc_hi = bootstrap_ci(accuracy_score, y_true_all, y_pred_all)
    f1_lo, f1_hi = bootstrap_ci(f1_score, y_true_all, y_pred_all, average='macro', zero_division=0)

    # Dummy baseline
    dummy_preds = []
    for train_idx, test_idx in loo.split(X_all):
        y_tr = y[train_idx]
        dummy = DummyClassifier(strategy='most_frequent', random_state=42)
        dummy.fit(np.zeros((len(y_tr), 1)), y_tr)
        dummy_preds.append(dummy.predict(np.zeros((1, 1)))[0])
    dummy_preds = np.array(dummy_preds)
    dummy_acc = accuracy_score(y_true_all, dummy_preds)

    # --- 打印 ---
    target_names = [labels_dict.get(i, str(i))
                    for i in sorted(set(y_true_all) | set(y_pred_all))]
    print(f'\\n  Accuracy:      {acc:.4f}  95% CI [{acc_lo:.2%}, {acc_hi:.2%}]')
    print(f'  Macro F1:      {f1_m:.4f}  95% CI [{f1_lo:.2%}, {f1_hi:.2%}]')
    print(f'  Macro Prec:    {prec_m:.4f}')
    print(f'  Macro Recall:  {rec_m:.4f}')
    if n_classes == 2:
        print(f'  AUC-ROC:       {auc_v:.4f}  95% CI [{auc_lo:.2%}, {auc_hi:.2%}]')
    else:
        print(f'  Macro AUC:     {auc_v:.4f}')
    print(f'  Dummy (most_frequent): {dummy_acc:.4f}  delta = {acc - dummy_acc:+.4f}')
    print(f'\\n  分类报告:')
    print(classification_report(y_true_all, y_pred_all, target_names=target_names, zero_division=0))

    cm = confusion_matrix(y_true_all, y_pred_all)
    results[dim_name] = {
        'accuracy': acc, 'acc_ci_low': acc_lo, 'acc_ci_high': acc_hi,
        'f1_macro': f1_m, 'f1_ci_low': f1_lo, 'f1_ci_high': f1_hi,
        'precision_macro': prec_m, 'recall_macro': rec_m,
        'auc': auc_v, 'auc_ci_low': auc_lo, 'auc_ci_high': auc_hi,
        'dummy_acc': dummy_acc,
        'y_true': y_true_all, 'y_pred': y_pred_all, 'y_proba': y_proba_all,
        'confusion_matrix': cm, 'labels': target_names, 'n_classes': n_classes,
    }

    # 全量训练 + 特征重要性
    scaler_full = StandardScaler()
    X_fs = scaler_full.fit_transform(X_all.values)
    rf_full = RandomForestClassifier(n_estimators=100, max_depth=5,
                                      min_samples_leaf=3, class_weight='balanced',
                                      random_state=42)
    rf_full.fit(X_fs, y)
    all_feature_importances[dim_name] = rf_full.feature_importances_

# ============================================================
# 5. 增强版汇总表
# ============================================================
print(f'\\n{\"=\"*100}')
print('*** MBTI 四维预测完整评估结果 ***')
print(f'{\"=\"*100}')
hdr = (f'{\"Dimension\":<22} {\"Acc\":>7} {\"Acc 95%CI\":>18} '
       f'{\"F1\":>6} {\"F1 95%CI\":>18} '
       f'{\"AUC\":>6} {\"AUC 95%CI\":>18} '
       f'{\"Dummy\":>6} {\"Delta\":>7}')
print(hdr)
print('-' * len(hdr))
for dim_name, tinfo in TARGETS.items():
    r = results[dim_name]
    auc_s = f'{r[\"auc\"]:.3f}' if not np.isnan(r['auc']) else 'N/A'
    auc_ci_s = f'[{r[\"auc_ci_low\"]:.2%},{r[\"auc_ci_high\"]:.2%}]' if not np.isnan(r['auc']) else 'N/A'
    print(f'{dim_name:<22} {r[\"accuracy\"]:>6.2%} [{r[\"acc_ci_low\"]:.2%},{r[\"acc_ci_high\"]:.2%}] '
          f'{r[\"f1_macro\"]:>5.3f} [{r[\"f1_ci_low\"]:.2%},{r[\"f1_ci_high\"]:.2%}] '
          f'{auc_s:>6} {auc_ci_s:>18} '
          f'{r[\"dummy_acc\"]:>5.2%} {r[\"accuracy\"]-r[\"dummy_acc\"]:>+7.2%}')
print('-' * len(hdr))
print(f'{\"Average\":<22} '
      f'{np.mean([r[\"accuracy\"] for r in results.values()]):>6.2%} '
      f'{np.mean([r[\"f1_macro\"] for r in results.values()]):>48.3f}')

# ============================================================
# 6. 混淆矩阵
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(11, 10))
axes = axes.flatten()
for idx, (dim_name, res) in enumerate(results.items()):
    ax = axes[idx]
    ConfusionMatrixDisplay(res['confusion_matrix'], display_labels=res['labels']).plot(
        ax=ax, cmap='Blues', values_format='d', colorbar=False)
    ax.set_title(f'{dim_name}\\nAcc={res[\"accuracy\"]:.1%}  F1={res[\"f1_macro\"]:.3f}', fontsize=11)
plt.tight_layout()
plt.savefig('output_confusion_matrices.png', dpi=150, bbox_inches='tight')
plt.close()
print('\\n[图表] 混淆矩阵已保存: output_confusion_matrices.png')

# ============================================================
# 7. ROC 曲线
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(11, 10))
axes = axes.flatten()
for idx, (dim_name, res) in enumerate(results.items()):
    ax = axes[idx]
    yt, yp, nc = res['y_true'], res['y_proba'], res['n_classes']
    if nc == 2:
        fpr, tpr, _ = roc_curve((yt == 2).astype(int), yp[:, 1])
        ax.plot(fpr, tpr, color='#FF6B8A', lw=2.5, label=f'AUC={auc(fpr,tpr):.3f}')
        ax.fill_between(fpr, tpr, alpha=0.12, color='#FF6B8A')
        ax.plot([0,1],[0,1],'k--',lw=1,alpha=0.35,label='Random')
    else:
        colors = ['#FF6B8A','#4ECDC4','#FFD93D']
        y_bin = label_binarize(yt, classes=sorted(np.unique(yt)))
        for ic, c in enumerate(sorted(np.unique(yt))):
            fpr, tpr, _ = roc_curve(y_bin[:,ic], yp[:,ic])
            ax.plot(fpr,tpr,color=colors[ic],lw=1.5,alpha=0.85,
                    label=f'{res[\"labels\"][ic]} AUC={auc(fpr,tpr):.3f}')
        ax.plot([0,1],[0,1],'k--',lw=1,alpha=0.35)
    ax.set_xlabel('FPR'); ax.set_ylabel('TPR')
    ax.set_title(f'{dim_name}', fontsize=12)
    ax.legend(fontsize=8, loc='lower right')
    ax.set_xlim([-0.02,1.02]); ax.set_ylim([-0.02,1.02])
    ax.grid(alpha=0.2)
plt.tight_layout()
plt.savefig('output_roc_curves.png', dpi=150, bbox_inches='tight')
plt.close()
print('[图表] ROC曲线已保存: output_roc_curves.png')

# ============================================================
# 8. 指标对比柱状图
# ============================================================
fig, ax = plt.subplots(figsize=(9, 5))
dim_short = ['E/I', 'S/N', 'T/F', 'J/P']
x = np.arange(4); w = 0.2
accs = [results[d]['accuracy'] for d in TARGETS]
f1s  = [results[d]['f1_macro'] for d in TARGETS]
aucs = [results[d]['auc'] if not np.isnan(results[d]['auc']) else 0 for d in TARGETS]
dums = [results[d]['dummy_acc'] for d in TARGETS]
b1 = ax.bar(x-1.5*w, accs, w, label='Accuracy', color='#FF6B8A', edgecolor='white')
b2 = ax.bar(x-0.5*w, f1s,  w, label='Macro F1', color='#FFB7B2', edgecolor='white')
b3 = ax.bar(x+0.5*w, aucs, w, label='AUC', color='#4ECDC4', edgecolor='white')
b4 = ax.bar(x+1.5*w, dums, w, label='Dummy', color='#E0E0E0', edgecolor='white', hatch='//')
ax.set_xticks(x); ax.set_xticklabels(dim_short, fontsize=12)
ax.set_ylabel('Score'); ax.set_title('MBTI四维预测指标对比 (LOOCV)', fontsize=13)
ax.legend(fontsize=9, loc='lower right'); ax.set_ylim(0,1.05)
ax.axhline(0.5, color='gray', ls='--', alpha=0.3)
ax.grid(axis='y', alpha=0.2)
for bars in [b1,b2,b3]:
    for b in bars:
        h = b.get_height()
        if h > 0.04:
            ax.text(b.get_x()+b.get_width()/2, h+0.012, f'{h:.2f}', ha='center', va='bottom', fontsize=7)
plt.tight_layout()
plt.savefig('output_metrics_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print('[图表] 指标对比图已保存: output_metrics_comparison.png')

# ============================================================
# 9. 特征重要性图
# ============================================================
feature_labels = ['餐饮伙食','社交娱乐','服饰美妆','学习发展','数码游戏',
                  '月生活费','兴趣投入','决策习惯','看重因素','性别','年级','生活费来源']
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()
for idx, (dim_name, imp) in enumerate(all_feature_importances.items()):
    ax = axes[idx]
    si = np.argsort(imp)[::-1][:10]
    colors = plt.cm.RdYlGn(imp[si]/imp[si].max())
    bars = ax.barh(range(len(si)), imp[si][::-1], color=colors[::-1], edgecolor='white')
    ax.set_yticks(range(len(si)))
    ax.set_yticklabels([feature_labels[i] for i in si[::-1]], fontsize=10)
    ax.set_title(dim_name, fontsize=12); ax.invert_yaxis()
    for bar, v in zip(bars, imp[si][::-1]):
        ax.text(bar.get_width()+0.005, bar.get_y()+bar.get_height()/2, f'{v:.3f}', va='center', fontsize=8)
plt.suptitle('MBTI 四维特征重要性', fontsize=14, y=1.01)
plt.tight_layout()
plt.savefig('output_feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()
print('[图表] 特征重要性图已保存: output_feature_importance.png')

# ============================================================
# 10. 关键发现
# ============================================================
print(f'\\n{\"=\"*60}')
print('关键发现')
print(f'{\"=\"*60}')
for dim_name, imp in all_feature_importances.items():
    top_i = np.argmax(imp)
    r = results[dim_name]
    auc_info = f'AUC={r[\"auc\"]:.3f}' if not np.isnan(r['auc']) else ''
    print(f'  {dim_name}: top_feat=\"{feature_labels[top_i]}\"(imp={imp[top_i]:.3f}), '
          f'Acc={r[\"accuracy\"]:.1%} CI[{r[\"acc_ci_low\"]:.2%},{r[\"acc_ci_high\"]:.2%}], '
          f'F1={r[\"f1_macro\"]:.3f} {auc_info}')

ei_imp = all_feature_importances['E/I (精力恢复)']
soc_i = FEATURE_COLS.index('consume_social')
dig_i = FEATURE_COLS.index('consume_digital')
print(f'\\n  假设验证:')
print(f'    \"社交花销大->E倾向\" : 社交重要性={ei_imp[soc_i]:.4f} (排名 {np.argsort(ei_imp)[::-1].tolist().index(soc_i)+1}/{len(FEATURE_COLS)})')
print(f'    \"数码花销大->I倾向\" : 数码重要性={ei_imp[dig_i]:.4f} (排名 {np.argsort(ei_imp)[::-1].tolist().index(dig_i)+1}/{len(FEATURE_COLS)})')

# ============================================================
# 11. 保存模型
# ============================================================
import pickle
for dim_name in TARGETS.keys():
    safe_name = dim_name.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '')
    y_full = df[TARGETS[dim_name]['col']].values
    sf = StandardScaler(); X_fs = sf.fit_transform(X_all.values)
    rf = RandomForestClassifier(n_estimators=100, max_depth=5,
                                 min_samples_leaf=3, class_weight='balanced', random_state=42)
    rf.fit(X_fs, y_full)
    pickle.dump(rf, open(f'model_rf_{safe_name}.pkl', 'wb'))
    pickle.dump(sf, open(f'model_scaler_{safe_name}.pkl', 'wb'))
pickle.dump(FEATURE_COLS, open('model_feature_cols_phase2.pkl', 'wb'))
print('[导出] 模型已保存')

print(f'\\nDone: phase2_mbti_classifier.py (v2) finished!')
'''

with open(new_file, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Written: {len(content)} chars')
