# 🎓 校园圈层聚类与推荐系统

> 基于 MBTI 心理特质与微观消费特征的校园圈层聚类与推荐系统  
> 机器学习课程大作业 · 2026 春

[![Python](https://img.shields.io/badge/Python-3.x-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.x-orange)](https://scikit-learn.org/)

---

## 📖 项目概述

在大学校园中，消费行为和性格特质是影响学生社交匹配的两个核心维度。本项目通过机器学习方法，利用学生消费行为数据自动识别校园群体类型，并预测 MBTI 性格维度，最终实现个性化的**校园搭子推荐系统**。

### 核心功能

- 🔍 **无监督聚类** — 使用 KMeans 对学生消费画像进行聚类分组
- 🧠 **MBTI 性格预测** — 使用随机森林从消费特征预测 E/I、S/N、T/F、J/P 四个维度
- 🤝 **搭子推荐** — 基于余弦相似度匹配，结合聚类圈层与 MBTI 性格给出推荐
- 🌐 **Web 应用** — Flask 后端 + 前端界面，支持问卷填写与实时推荐

---

## 📊 数据说明

问卷设计包含 **5 大模块、19 道题目**：

| 模块 | 内容 |
|------|------|
| 基础信息 | 性别、年级、生活费来源、月生活费区间 |
| 消费结构 | 餐饮伙食、社交娱乐、服饰美妆、学习发展、数码游戏 |
| 消费行为 | 决策习惯、选购看重因素、兴趣投入意愿 |
| MBTI 自测 | E/I 精力恢复、S/N 信息处理、T/F 决策标准、J/P 生活风格 |
| 社交偏好 | 交友偏好、搭子系统态度、结伴场景偏好 |

- 数据规模：69 份原始问卷 → 清洗后 **62 条有效记录**
- 数据文件：`data_cleaned.csv`（原始数据：`MBTI性格与大学生消费行为关联.xlsx`）

---

## 🏗️ 项目结构

```
├── phase1_clustering.py      # 阶段一：数据清洗 + KMeans 聚类
├── phase2_mbti_classifier.py # 阶段二：随机森林 MBTI 分类器
├── phase3_app.py             # 阶段三：Flask Web 应用
├── phase3_apptest.py         # 阶段三：模型测试脚本
├── app.py                    # Flask 后端主入口
├── generate_report.py        # 实验报告自动生成
├── gen_*.py                  # SVG/图表/PPT 生成脚本
├── data_cleaned.csv          # 清洗后数据
├── cluster_summary.csv       # 聚类结果汇总
├── model_*.pkl               # 训练好的模型文件
├── output_*.png              # 模型评估可视化图表
├── templates/                # Flask HTML 模板
├── projects/                 # PPT 生成项目
└── *.docx / *.pptx           # 课程报告与汇报 PPT
```

---

## 🚀 快速开始

### 环境要求

- Python 3.x
- 依赖包：`flask`, `flask-cors`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `python-docx`

### 安装与运行

```bash
# 克隆仓库
git clone https://github.com/zzr005119/campus-mbti-clustering.git
cd campus-mbti-clustering

# 安装依赖
pip install flask flask-cors scikit-learn pandas numpy matplotlib seaborn python-docx

# 启动 Flask 应用
python app.py
```

---

## 📈 模型评估

| 指标 | 说明 |
|------|------|
| KMeans 聚类 | 肘部法则 + 轮廓系数确定最优 K 值 |
| 随机森林分类 | 四个 MBTI 维度独立建模 |
| 评估指标 | Accuracy、F1-score、AUC-ROC、混淆矩阵 |
| 置信区间 | 95% Bootstrap CI |
| 基线对比 | Dummy Classifier 基线 |

---

## 📁 输出成果

- 📄 课程实验报告（`.docx`）
- 📄 课程项目报告（`.docx`）
- 🎞️ 课堂汇报 PPT（`.pptx`）
- 📊 模型评估图表（PCA 降维、热力图、ROC 曲线、雷达图等）

---

## ⚠️ 注意事项

- `.env` 文件已加入 `.gitignore`，需自行创建并配置密钥
- 模型文件（`.pkl`）需与代码保持版本一致

---

## 📝 License

本项目为课程作业，仅供学习参考。
