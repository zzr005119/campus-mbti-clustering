
import pandas as pd
df = pd.read_excel('MBTI性格与大学生消费行为关联.xlsx')
mbti_cols = ['13. 经过一周的疲惫学习，你更倾向于哪种精力恢复方式?',
             '14. 在接收和处理信息时，你更倾向于?',
             '15. 在做决定时，你的评判标准通常是?',
             '16. 你的日常行事与生活风格是?']
mask = df[mbti_cols].nunique(axis=1) == 1
print(df[mask][['序号'] + mbti_cols + ['所用时间']].to_string())
"