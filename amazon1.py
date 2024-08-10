#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 21 23:00:03 2024

@author: lygt
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
from random import random
import time


## optimize response by setting custom_headers
custom_headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept': '*/*',
    'Referer': 'https://www.amazon.com/'
    }

visited_urls = set()
## 配置 Selenium
# 请替换为你的 chromedriver 路径
chrome_driver_path = "/Users/lygt/Documents/data scientsist learning/techlent/homework/project/chrome-mac-x64"  
service = Service(chrome_driver_path)
options = Options()
options.add_argument("--headless")  # 无头模式
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

def get_product_info(url, idx):
    """
    获取每个产品页面的产品信息
    """
    try:
        # 使用Selenium获取网页
        with webdriver.Chrome(service=service, options=options) as browser:
            browser.get(url)
            time.sleep(3)  # 等待页面加载

            # 保存Selenium抓取的页面信息
            output_path = f'/Users/lygt/Documents/data scientsist learning/techlent/homework/project/url link/amazon_{idx}_selenium.html'
            with open(output_path, 'w', encoding='utf-8') as fw:
                fw.write(browser.page_source)

        # 读取本地保存的HTML文件
        input_path = f'/Users/lygt/Documents/data scientsist learning/techlent/homework/project/url link/amazon_{idx}_selenium.html'
        with open(input_path, 'r', encoding='utf-8') as file:
            page_content = file.read()

        soup = BeautifulSoup(page_content, 'lxml')

        # 提取商品标题
        title_element = soup.select_one('#productTitle')
        title = title_element.text.strip() if title_element else None

        # 提取商品评价分数
        rating_element = soup.select_one('#acrPopover')
        rating_text = rating_element.attrs.get('title') if rating_element else None
        rating = rating_text.replace('out of 5 stars', '').strip() if rating_text else None

        # 提取商品价格
        price_element = soup.select_one('span.a-offscreen')
        price = price_element.text.strip() if price_element else None

        # 获取产品描述
        description_element = soup.select_one('#productDescription')
        description = description_element.text.strip() if description_element else None

        # 提取商品评价数目
        review_num_element = soup.select_one('#acrCustomerReviewText')
        review_num = review_num_element.text.replace(' ratings', '').strip() if review_num_element else None

        # 获取产品详细信息
        table = soup.find("table", class_="a-normal a-spacing-micro")
        if table:
            product_detail_title_elements = table.find_all('span', class_="a-size-base a-text-bold")
            product_detail_elements = table.find_all('span', class_="a-size-base po-break-word")
            detail_dict = {title.text.strip(): detail.text.strip() for title, detail in zip(product_detail_title_elements, product_detail_elements)}

            brand = detail_dict.get('Brand')
            psupplement_type = detail_dict.get('Primary Supplement Type')
            ingredient = detail_dict.get('Special Ingredients')
            diet_type = detail_dict.get('Diet Type')
            benefits = detail_dict.get('Product Benefits')
            age = detail_dict.get('Age Range')
        else:
            brand, psupplement_type, ingredient, diet_type, benefits, age = [None] * 6

        # 获取评论信息
        review_elements = soup.select("div.review")
        scraped_reviews = []

        for review in review_elements:
            r_author = review.select_one("span.a-profile-name")
            r_rating = review.select_one("i.review-rating")
            r_title = review.select_one("a.review-title span:not([class])")
            r_content = review.select_one("span.review-text")
            r_date = review.select_one("span.review-date")
            r_verified = review.select_one("span.a-size-mini")

            r = {
                "Review_Author": r_author.text if r_author else None,
                "Review_Rating": r_rating.text.replace("out of 5 stars", "").strip() if r_rating else None,
                "Review_Title": r_title.text if r_title else None,
                "Review_Content": r_content.text if r_content else None,
                "Review_Date": r_date.text if r_date else None,
                "Review_Verified": r_verified.text if r_verified else None
            }

            scraped_reviews.append(r)

        data = {
            "Title": title,
            "Rating": rating,
            "Price": price,
            "Description": description,
            "Review number": review_num,
            "Brand": brand,
            "Primary Supplement Type": psupplement_type,
            "Special Ingredients": ingredient,
            "Diet Type": diet_type,
            "Product Benefits": benefits,
            "Age Range": age,
            "Review Information": scraped_reviews,
            "url": url
        }
        return data
    except Exception as e:
        print(f"Error fetching product info for {url}: {e}")
        return None

def parse_listing(listing_url):
    """
    获取搜索页面中的所有链接地址
    """
    global visited_urls

    with webdriver.Chrome(service=service, options=options) as browser:
        browser.get(listing_url)
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-asin] h2 a")))
        soup_search = BeautifulSoup(browser.page_source, "lxml")
    
    link_elements = soup_search.select("[data-asin] h2 a")
    df_sum = pd.DataFrame()

    for idx, link in enumerate(link_elements, 1):
        full_url = urljoin(listing_url, link.attrs.get("href"))
        if full_url not in visited_urls:
            visited_urls.add(full_url)
            print(f"正在抓取第 {idx} 个产品: {full_url[:100]}", flush=True)
            product_info = get_product_info(full_url, idx)
            if product_info:
                df_now = pd.DataFrame([product_info])
                reviews_df = pd.json_normalize(product_info['Review Information'])
                combined_df = pd.concat([df_now.drop(columns='Review Information'), reviews_df], axis=1)
                df_sum = pd.concat([df_sum, combined_df], ignore_index=True)
            # 休眠
            time.sleep(1 + 2 * random.random())
        # 只抓取48个产品
        if idx >= 48:
            break

    return df_sum

def main():
    search_url = "https://www.amazon.sg/s?k=vitamins+dietary+healthy+supplement&ref=nb_sb_noss"
    data = parse_listing(search_url)
    output_path = '/Users/lygt/Documents/data scientsist learning/techlent/homework/project/vitamin.csv'
    data.to_csv(output_path, index=False, encoding='utf-8')
    print("数据已保存到 vitamin.csv")

if __name__ == '__main__':
    main()