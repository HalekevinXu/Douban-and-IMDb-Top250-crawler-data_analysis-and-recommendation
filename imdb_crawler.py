import re
import time
import random
import csv
import json
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from lxml import etree
from lxml import html
import os
from webdriver_manager.chrome import ChromeDriverManager



def main(f):
    # 配置Chrome浏览器选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式，不显示浏览器窗口
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.35 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
     # 使用WebDriver Manager自动管理驱动
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 程序开始时创建用于存评论的文件
    create_reviews_file()

    try:
        # 访问IMDb Top 250页面
        driver.get('https://www.imdb.com/chart/top/')
        print("等待页面加载完成...")
        
        # 显式等待主要内容加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.ipc-metadata-list"))
        )
        
        # # 保存页面用于调试
        # with open('imdb_debug.html', 'w', encoding='utf-8') as debug_file:
        #     debug_file.write(driver.page_source)
        #     print(f"调试文件已保存到: {os.path.abspath('imdb_debug.html')}")
        
        # 使用lxml解析页面
        tree = etree.HTML(driver.page_source)
        
        # 获取所有电影条目
        movies = tree.xpath('//ul[contains(@class, "ipc-metadata-list")]/li')
        print(f"找到 {len(movies)} 部电影")
        
        if len(movies) != 250:
            print(f"错误：只找到 {len(movies)} 部电影，而不是250部。终止程序。")
            driver.quit()
            sys.exit(1)  


        # 提取每部电影的链接和名称
        for movie in movies:   
            try:
                # 获取电影名称
                name_element = movie.xpath('.//h3[contains(@class, "ipc-title__text")]')
                if not name_element:
                    continue
                name = name_element[0].text.split('. ', 1)[-1]  # 移除排名编号
                
                # 获取详情页链接
                href_element = movie.xpath('.//a[contains(@href, "/title/")]/@href')
                if not href_element:
                    continue
                href = "https://www.imdb.com" + href_element[0].split('?')[0]  # 基础URL
                
                print(f"正在爬取: {name} - {href}")
                get_info(driver, href, name, f)  # 获取详情信息
                time.sleep(random.uniform(2, 5))  # 随机延时
                
            except Exception as e:
                print(f"处理电影时出错: {str(e)}")
                continue
                
    finally:
        driver.quit()  # 确保浏览器关闭
    print('爬取完毕')

def get_info(driver, url, name, f):
    try:
        # 访问详情页
        driver.get(url)
        print(f"正在加载详情页: {name}")
        
        # 等待关键元素加载
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='title-details-section']"))
        )

        # # 保存页面用于调试
        # debug_file_path = f"imdb_debug_{name.replace(' ', '_')}.html"
        # with open(debug_file_path, 'w', encoding='utf-8') as debug_file:
        #     debug_file.write(driver.page_source)
        #     print(f"详情页HTML已保存到: {os.path.abspath(debug_file_path)}")

        # 解析页面
        tree = etree.HTML(driver.page_source)
        
        # 导演信息
        director = tree.xpath('//*[@id="__next"]/main/div/section[1]/section/div[3]/section/section/div[3]/div[2]/div[1]/section/div[2]/ul/li[1]/div/ul/li/a/text()')
        director = director[0] if director else "N/A"

        #主演信息
        # 精确选择包含"Stars"文本的列表项
        
        stars_xpath = '''
            //li[@data-testid="title-pc-principal-credit"][.//a[normalize-space()="Stars"]][1]
            //a[contains(@class, "ipc-metadata-list-item__list-content-item")]/text()
            '''

        stars = tree.xpath(stars_xpath)
        # 去重处理
        stars = list(dict.fromkeys(stars))
        stars = " / ".join(stars)

        # 电影类型
        genres = extract_genres(driver)
        #以下方式无法获取
        # genres = re.findall(r'<a class="ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link" tabindex="0" aria-disabled="false" href="/search/title/?genres=Action&amp;explore=genres&amp;ref_=tt_stry_gnr">(.*?)</a>',driver.page_source)
        # genres = '/'.join(genres) if genres else "N/A"
        # genres = tree.xpath('.//ul[contains(@class, "ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link")]')
        # genres = '/'.join(genres) if genres else "N/A"
        
        # 国家
        countries = tree.xpath('//li[@data-testid="title-details-origin"]//li[@class="ipc-inline-list__item"]/a/text()')
        countries = "/".join(countries)
        
        # 以下方式无法获取        
        # countries = tree.xpath('//*[@id="__next"]/main/div/section[1]/div/section/div/div[1]/section[11]/div[2]/ul/li[2]/div/text()')
        # countries = '/'.join(countries) if countries else "N/A"
        
        # 上映年份          
        year = tree.xpath('//*[@id="__next"]/main/div/section[1]/section/div[3]/section/section/div[2]/div[1]/ul/li[1]/a/text()')
        year = re.search(r'\d{4}', year[0]).group() if year else "N/A"
        
        # 片长
        runtime = tree.xpath('//*[@id="__next"]/main/div/section[1]/section/div[3]/section/section/div[2]/div[1]/ul/li[3]/text()')
        runtime = runtime[0].strip() if runtime else "N/A"
        
        # 评分
        rating = tree.xpath("//div[@data-testid='hero-rating-bar__aggregate-rating__score']/span[1]/text()")
        rating = rating[0] if rating else "N/A"
        
        # 评分人数
        rating_count = tree.xpath('//*[@id="__next"]/main/div/section[1]/section/div[3]/section/section/div[2]/div[2]/div/div[1]/a/span/div/div[2]/div[3]/text()')
        rating_count = rating_count[0].replace(',', '') if rating_count else "N/A"

        #全球票房
        gross_worldwide = tree.xpath('//span[contains(text(), "Gross worldwide")]/following::span[contains(@class, "ipc-metadata-list-item__list-content-item")][1]/text()')
        gross_worldwide = gross_worldwide[0].strip() if gross_worldwide else "N/A"

        #精选评论
        featured_reviews = get_featured_reviews(driver)
        #保存评论
        save_reviews_to_file(name, featured_reviews)
        print(f"已保存 {len(featured_reviews)} 条精选评论到 imdb_reviews.txt")

        #其他信息打印与保存
        print(name, director, stars, genres, countries, year, runtime, rating, rating_count, gross_worldwide)
        csvwriter.writerow((name, director, stars, genres, countries, year, runtime, rating, rating_count, gross_worldwide))
        f.flush()
        
    except Exception as e:
        print(f"爬取详情页出错: {url} - {str(e)}")


def extract_genres(driver):
    """从JSON-LD结构化数据中提取电影类型"""
    try:
        # 定位JSON-LD脚本标签
        script_element = driver.find_element(
            By.XPATH, 
            "//script[@type='application/ld+json']"
        )
        
        # 解析JSON数据
        json_data = json.loads(script_element.get_attribute("innerHTML"))
        
        # 提取体裁数组
        genres = json_data.get("genre", [])
        
        return '/'.join(genres) if genres else "N/A"
    
    except Exception as e:
        print(f"从JSON-LD提取电影类型失败: {str(e)}")
        return "N/A"


def get_featured_reviews(driver):
     # 等待精选评论加载
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-testid="user-reviews-summary-featured-review-card"]'))
        )
    except TimeoutException:
        print("精选评论未加载或不存在")
        return []
        
    tree = html.fromstring(driver.page_source)
        
    # 定位精选评论卡片
    review_cards = tree.xpath('//div[@data-testid="user-reviews-summary-featured-review-card"]')
        
    if not review_cards:
        print("未找到精选评论卡片")
        return []
        
    reviews = []
    for review_card in review_cards:    
        # 提取评分
        rating_elements = review_card.xpath('.//span[contains(@class, "ipc-rating-star")]/span[@class="ipc-rating-star--rating"]')
        rating = rating_elements[0].text if rating_elements else "N/A"
            
        # 提取作者
        #author_elements = review_card.xpath('.//a[contains(@class, "user-reviews-summary-featured-review-author")]')
        #author = author_elements[0].text.strip() if author_elements else "N/A"
            
        # 提取评论标题
        title_elements = review_card.xpath('.//h3[@class="ipc-title__text ipc-title__text--reduced"]')
        title = title_elements[0].text.strip() if title_elements else "N/A"
            
        # 提取评论正文
        content_divs = review_card.xpath('.//div[@class="ipc-html-content-inner-div"]')
            
        if content_divs:
            content_div = content_divs[0]
            content_html = html.tostring(content_div, encoding='unicode')
            content_text = re.sub(r'<br\s*/?>', '\n', content_html, flags=re.IGNORECASE)
            content_text = re.sub(r'<[^>]+>', '', content_text).strip()
        else:
            content_text = "N/A"
        
        #构造评论字典
        review = {
            "rating": rating,
            #"author": author,
            "title": title,
            "content": content_text
        }
        reviews.append(review)
    
    return reviews

# 在程序开始时创建文件并写入表头
def create_reviews_file():
    with open("imdb_reviews.txt", "w", encoding="utf-8") as f:
        f.write("IMDB Movie Reviews Collection\n")
        f.write("=" * 50 + "\n\n")

# 在爬取每部电影时追加评论
def save_reviews_to_file(name, featured_reviews):
        # 评论保存到文本文件
        with open('imdb_reviews.txt', "a", encoding="utf-8") as f:
            # 第一行写入电影名
            f.write(f"{name}\n\n")
        
            # 写入每条评论
            for i, review in enumerate(featured_reviews, 1):
                f.write(f"精选评论 {i}:\n")
                f.write(f"评分: {review['rating']}\n")
                #f.write(f"作者: {review['author']}\n")
                f.write(f"标题: {review['title']}\n")
                f.write(f"内容:\n{review['content']}\n\n")
        
            # 所有评论结束后空两行
            f.write("\n\n\n")
        
 
if __name__ == '__main__':

    # 创建CSV文件
    output_path = 'imdb_top_250.csv'
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        csvwriter = csv.writer(f)
        csvwriter.writerow(('电影名称', '导演', '主演', '电影类型', '国家', '上映年份', '片长', '评分', '评论人数', '全球票房'))
        main(f)