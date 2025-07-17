import re
from time import sleep
import requests
from lxml import etree
import random
import csv



def main(page, f):
    url = f'https://movie.douban.com/top250?start={page * 25}&filter='  # 发起网络请求
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.35 Safari/537.36', }  # 模仿浏览器访问页面
    resp = requests.get(url, headers=headers)
    tree = etree.HTML(resp.text)  # 将变量装入解释器

    href_list = tree.xpath('//*[@id="content"]/div/div[1]/ol/li/div/div[1]/a/@href')  # 获取详情页的链接列表，跳转到详情页面

    name_list = tree.xpath('//*[@id="content"]/div/div[1]/ol/li/div/div[2]/div[1]/a/span[1]/text()')  # 获取电影名称列表
    for url, name in zip(href_list, name_list):  # 遍历
        f.flush()  # 刷新文件
        try:
            get_info(url, name)  # 获取详情页的信息
        except:
            pass
    print(f'第{i + 1}页爬取完毕')


def get_info(url, name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.35 Safari/537.36',
        # 模仿浏览器访问页面
        'Host': 'movie.douban.com',
    }
    resp = requests.get(url, headers=headers)
    html = resp.text
    tree = etree.HTML(html)

    ranking = tree.xpath('//*[@id="content"]/div[1]/span[1]/text()')[0]  # 排名
    ditr = tree.xpath('//*[@id="info"]/span[1]/span[2]/a/text()')[0]  # 导演

    type_ = re.findall(r'property="v:genre">(.*?)</span>', html)  # 电影类型
    type_ = '/'.join(type_)

    country = re.findall(r'地区:</span> (.*?)<br', html)[0]  # 国家

    time = tree.xpath('//*[@id="content"]/h1/span[2]/text()')[0]  # 上映时间
    time = time[1:5]
    length = tree.xpath('//*[@id="info"]/span[13]/text()')[0]  # 片长

    rate = tree.xpath('//*[@id="interest_sectl"]/div[1]/div[2]/strong/text()')[0]  # 评分

    five = tree.xpath('//*[@id="interest_sectl"]/div[1]/div[3]/div[1]/span[2]/text()')[0]  # 五星
    four = tree.xpath('//*[@id="interest_sectl"]/div[1]/div[3]/div[2]/span[2]/text()')[0]  # 四星
    three = tree.xpath('//*[@id="interest_sectl"]/div[1]/div[3]/div[3]/span[2]/text()')[0]  # 三星
    two = tree.xpath('//*[@id="interest_sectl"]/div[1]/div[3]/div[4]/span[2]/text()')[0]  # 二星
    one = tree.xpath('//*[@id="interest_sectl"]/div[1]/div[3]/div[5]/span[2]/text()')[0]  # 一星

    people = tree.xpath('//*[@id="interest_sectl"]/div[1]/div[2]/div/div[2]/a/span/text()')[0]  # 评论人数

    print(name, ranking, ditr, type_, country, time, length, rate, five, four, three, two, one, people)
    csvwriter.writerow((name, ranking, ditr, type_, country, time, length, rate, five, four, three, two, one, people))


if __name__ == '__main__':

    # 创建文件用于保存数据
    with open('豆瓣电影2.csv', 'a', encoding='utf-8', newline='')as f:
        csvwriter = csv.writer(f)
        csvwriter.writerow(('电影名称', '排名', '导演', '电影类型', '国家', '上映年份', '片长', '评分', '五星', '四星', '三星', '二星', '一星', '评论人数'))
        #         csvwriter.writerow(('电影名称','排名', '导演', '电影类型', '国家', '上映年份', '评分', '评论人数')) # 写入表头标题
        for i in range(3,10):  # 创建循环，爬取10页数据
            main(i, f)  # 调用主函数

