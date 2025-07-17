import pandas as pd
from scipy import stats

df_db = pd.read_csv('豆瓣电影.csv',encoding='gbk')
df_db["评分"] = pd.to_numeric(df_db["评分"], errors="coerce")
df_imdb = pd.read_csv('imdb_top_250_纯中文.csv',encoding='gbk')
df_imdb["评分"] = pd.to_numeric(df_imdb["评分"], errors="coerce")

#计算函数
def describe_distribution(series, name=""):
    """返回一个包含五统计量的字典"""
    return {
        "平台": name,
        "均值": series.mean(),
        "中位数": series.median(),
        "标准差": series.std(ddof=0),   # 总体标准差
        "偏度": stats.skew(series, bias=False),   # 无偏估计
        "峰度": stats.kurtosis(series, bias=False)  # Fisher 无偏估计（正态为 0）
    }

#计算并汇总
stats_db   = describe_distribution(df_db["评分"].dropna(),   "豆瓣")
stats_imdb = describe_distribution(df_imdb["评分"].dropna(), "IMDb")

# 继续你的代码
summary = pd.DataFrame([stats_db, stats_imdb]).set_index('平台')
print(summary.round(3).to_markdown())