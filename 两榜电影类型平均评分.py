import pandas as pd

# 读取两个CSV文件
df_douban = pd.read_csv('豆瓣电影.csv', encoding='gbk')
df_imdb = pd.read_csv('imdb_top_250_纯中文.csv', encoding='gbk')

# 定义一个函数来处理电影类型列，将其拆分为单独的类型
def split_genres(genres):
    return [genre.strip() for genre in genres.split('/') if genre.strip()]

# 处理豆瓣电影类型的列
df_douban['类型列表'] = df_douban['电影类型'].apply(split_genres)

# 处理IMDb电影类型的列
df_imdb['电影类型'] = df_imdb['电影类型'].str.replace(' / ', '/')
df_imdb['类型列表'] = df_imdb['电影类型'].apply(split_genres)

# 初始化一个空的列表来存储结果
result_list = []

# 计算豆瓣电影的平均评分
for genre in set([item for sublist in df_douban['类型列表'] for item in sublist]):
    genre_df = df_douban[df_douban['类型列表'].apply(lambda x: genre in x)]
    avg_rating_douban = genre_df['评分'].mean().round(2)
    result_list.append({'类型': genre, '豆瓣平均评分': avg_rating_douban, 'IMDb平均评分': None})

# 计算IMDb电影的平均评分
for genre in set([item for sublist in df_imdb['类型列表'] for item in sublist]):
    genre_df = df_imdb[df_imdb['类型列表'].apply(lambda x: genre in x)]
    avg_rating_imdb = genre_df['评分'].mean().round(2)
    for row in result_list:
        if row['类型'] == genre:
            row['IMDb平均评分'] = avg_rating_imdb

# 转换结果列表为DataFrame
result = pd.DataFrame(result_list)
result.to_csv('两榜电影类型平均评分.csv', index=False)