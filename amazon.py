#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 08:19:43 2024

@author: lygt
"""

import requests
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

def get_product_info(url):
    """
    get the product information from each product page
    """

    response = requests.get(url, headers=custom_headers)
    if response.status_code != 200:
        print(f"Error in getting webpage: {url}")
        return None
    
    soup = BeautifulSoup(response.text, 'lxml')
    
    ## get the product title
    title_element = soup.select_one('#productTitle')
    title = title_element.text.strip() if title_element else None
    #print(title)
    
    ## get the product rating
    rating_element = soup.select_one('#acrPopover')
    rating_text = rating_element.attrs.get('title') if rating_element else None
    rating = rating_text.replace('out of 5 stars','')
    #print(rating)
    
    ## get the product price
    price_element = soup.select_one('span.a-offscreen')
    price = price_element.text if price_element else None
    #print(price)
    
    ## get the description of product
    description_element = soup.select_one('#productDescription')
    description = description_element.text.strip() if description_element else None
    #print(description)
    
    ## get the review number
    review_num_element = soup.select_one('#acrCustomerReviewText')
    review_num = review_num_element.text.replace(' ratings','') if review_num_element else None
    #print(review_num)
    
    ## get the other information of product details
    table = soup.find("table", class_ = "a-normal a-spacing-micro")
    
    product_detail_title_element = table.find_all('span', class_ = "a-size-base a-text-bold")
    product_detail_element = table.find_all('span', class_ = "a-size-base po-break-word")
    print(len(product_detail_title_element), len(product_detail_element))
    brand, psupplement_type,ingredient,diet_type,benefits, age = '','','','','',''
    
    for i in range(len(product_detail_element)):
        
        if product_detail_title_element[i].text == 'Brand':
            brand = product_detail_element[i].text
        
        if product_detail_title_element[i].text == 'Primary Supplement Type':
            psupplement_type = product_detail_element[i].text
            
        if product_detail_title_element[i].text == 'Special Ingredients':
            ingredient = product_detail_element[i].text
            
        if product_detail_title_element[i].text == 'Diet Type':
            diet_type = product_detail_element[i].text
            
        
        if product_detail_title_element[i].text == 'Product Benefits':
            benefits = product_detail_element[i].text
            
    
        if product_detail_title_element[i].text == 'Age Range':
            age = product_detail_element[i].text

    if not brand: brand = None
    if not psupplement_type: psupplement_type = None
    if not ingredient: ingredient = None
    if not diet_type: diet_type = None
    if not benefits: benefits = None
    if not age: age = None
    print(brand, psupplement_type,ingredient,diet_type,benefits, age)
    
    ## get review elements
    review_elements = soup.select("div.review")

    scraped_reviews = []

    for review in review_elements:
        r_author_element = review.select_one("span.a-profile-name")
        r_author = r_author_element.text if r_author_element else None

        r_rating_element = review.select_one("i.review-rating")
        r_rating = r_rating_element.text.replace("out of 5 stars", "") if r_rating_element else None

        r_title_element = review.select_one("a.review-title")
        r_title_span_element = r_title_element.select_one("span:not([class])") if r_title_element else None
        r_title = r_title_span_element.text if r_title_span_element else None

        r_content_element = review.select_one("span.review-text")
        r_content = r_content_element.text if r_content_element else None

        r_date_element = review.select_one("span.review-date")
        r_date = r_date_element.text if r_date_element else None

        r_verified_element = review.select_one("span.a-size-mini")
        r_verified = r_verified_element.text if r_verified_element else None

        #r_image_element = review.select_one("img.review-image-tile")
        #r_image = r_image_element.attrs["src"] if r_image_element else None

        r = {
            "Review_Author": r_author,
            "Review_Rating": r_rating,
            "Review_Title": r_title,
            "Review_Content": r_content,
            "Review_Date": r_date,
            "Review_Verified": r_verified,
            #"image_url": r_image
        }

        scraped_reviews.append(r)

    data = {"Title": title,
            "Rating": rating,
            "Price": price,
            "Description": description,
            "Review number": review_num,
            "Brand": brand,
            "Primary Supplement Type":psupplement_type,
            "Special Ingredients": ingredient,
            "Diet Type": diet_type,
            "Product Benefits": benefits,
            "Age Range": age,
            "Review Information": scraped_reviews,
            "url": url
            }
    return data


def parse_listing(listing_url):
    """
    get all the link address from the searching page
    """

    global visited_urls
    response = requests.get(listing_url, headers=custom_headers)
    print(response.status_code)
    soup_search = BeautifulSoup(response.text, "lxml")
    link_elements = soup_search.select("[data-asin] h2 a")
    page_data = []
    j = 0
    df_sum = pd.DataFrame()
    

    for link in link_elements:
        j = j+1
        full_url = urljoin(listing_url, link.attrs.get("href"))
        if full_url not in visited_urls:
            visited_urls.add(full_url)
            print('now is product', j)
            print(f"Scraping product from {full_url[:100]}", flush=True)
            product_info = get_product_info(full_url)
            # convert to dataframe
            df_now = pd.DataFrame(product_info)
            # unnest Review column
            df_now = pd.concat([df_now, df_now['Review Information'].apply(pd.Series)], axis=1)
            if product_info:
                df_sum = pd.concat([df_sum, df_now], axis=0)
                df_now = pd.DataFrame()
            # sleep    
            for i in range(5):
                t = 1 + 2 * random()
                time.sleep(t)
        # scrape only 10 products
        if j > 10:
            return df_sum
    #next_page_el = soup_search.select_one('a.s-pagination-next')
    #if next_page_el:
    #    next_page_url = next_page_el.attrs.get('href')
    #    next_page_url = urljoin(listing_url, next_page_url)
    #    print(f'Scraping next page: {next_page_url}', flush=True)
    #    page_data += parse_listing(next_page_url)

    #return df_sum

def main():
    data = []
    search_url = "https://www.amazon.com/s?k=healthy+food+supplements&crid=TK78GUIGUSH5&sprefix=healthy+food+su%2Caps%2C415&ref=nb_sb_ss_pltr-sample-20_2_15"
    data = parse_listing(search_url)
    data = data.drop(['Review Information'], axis=1)
    #df = pd.concat([df.drop(['Review Information'], axis=1), df['Review Information'].apply(pd.Series)], axis=1)
    import os
    path = '/Users/lygt/Documents/data scientsist learning/techlent/homework/project'
    output_file = os.path.join(path,'healthy food supplement.csv')
    data.to_csv(output_file, index=False)


if __name__ == '__main__':
    main()   

