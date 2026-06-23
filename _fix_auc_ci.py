import os
path = r'D:\Xx\大二下\机器学习\大作业\phase2_mbti_classifier.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Change 1: find end of bootstrap_ci_auc function, insert new func after
insert_at = None
for i, line in enumerate(lines):
    if 'bootstrap_ci_auc' in line and 'def ' in line and 'multiclass' not in line:
        # find the end of this function (the return line)
        for j in range(i+1, min(i+20, len(lines))):
            if 'return np.percentile' in lines[j]:
                insert_at = j + 1
                break
        break

if insert_at:
    new_func = '\n'
    new_func += 'def bootstrap_ci_auc_multiclass(y_true, y_proba, n_bootstrap=2000, alpha=0.05):\n'
    new_func += '    """Bootstrap 95% CI for macro AUC-ROC (multi-class OvR)"""\n'
    new_func += '    n = len(y_true)\n'
    new_func += '    classes = sorted(np.unique(y_true))\n'
    new_func += '    scores = []\n'
    new_func += '    rng = np.random.RandomState(42)\n'
    new_func += '    for _ in range(n_bootstrap):\n'
    new_func += '        idx = rng.randint(0, n, n)\n'
    new_func += '        try:\n'
    new_func += '            y_bin = label_binarize(y_true[idx], classes=classes)\n'
    new_func += '            s = roc_auc_score(y_bin, y_proba[idx], average="macro", multi_class="ovr")\n'
    new_func += '        except ValueError:\n'
    new_func += '            s = 0.5\n'
    new_func += '        scores.append(s)\n'
    new_func += '    return np.percentile(scores, 100*alpha/2), np.percentile(scores, 100*(1-alpha/2))\n'
    new_func += '\n'
    lines.insert(insert_at, new_func)
    print(f'[1] Added bootstrap_ci_auc_multiclass after line {insert_at}')

# Change 2: replace np.nan, np.nan with function call
for i, line in enumerate(lines):
    if 'auc_lo, auc_hi = np.nan, np.nan' in line:
        lines[i] = '        auc_lo, auc_hi = bootstrap_ci_auc_multiclass(y_true_all, y_proba_all)\n'
        print(f'[2] Replaced np.nan at line {i+1}')
        break

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Done.')
