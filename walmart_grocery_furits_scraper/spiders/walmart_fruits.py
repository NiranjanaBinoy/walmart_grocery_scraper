# -*- coding: utf-8 -*-
import scrapy
import json
from scrapy.shell import inspect_response


class WalmartFruitsSpider(scrapy.Spider):
    name = 'walmart_fruits'
    allowed_domains = ['walmart.ca']
    start_urls = ['https://www.walmart.ca/en/grocery/fruits-vegetables/fruits/N-3852/']
    BASE_URL = 'https://www.walmart.ca'

    def parse(self, response):
        fruits_article_list = response.xpath('//*[@id="shelf-thumbs"]/div/article')
        for fruits_article in fruits_article_list:
            sub_url = fruits_article.xpath(
                './/*[@class="product-link"]/@href').extract_first()  # fetching the url for the individual page
            final_url = self.BASE_URL + sub_url
            yield scrapy.Request(final_url, callback=self.parse_individual_fruit)  # requesting the single fruit page

        # pagination
        next_page_url = response.xpath('//*[@id="loadmore"]/@href').extract_first()
        if next_page_url:
            absolute_next_url = response.urljoin(next_page_url)
            yield scrapy.Request(absolute_next_url, callback=self.parse)

    # callback method that parse through each page url
    def parse_individual_fruit(self, response):
        windows_preloaded_data = response.xpath('/html/body/script[1]/text()').extract()
        preloaded_json = json.loads('='.join(windows_preloaded_data[0].split('=')[1:]).rstrip(';'))
        sku = preloaded_json['product']['activeSkuId']

        image_list = preloaded_json['entities']['skus'][sku]['images']
        image_urls = []
        for image in image_list:
            image_urls.append(image['thumbnail']['url'])
            image_urls.append(image['small']['url'])
            image_urls.append(image['large']['url'])
            image_urls.append(image['enlarged']['url'])

        categories_list = preloaded_json['entities']['skus'][sku]['categories']
        category_hierarchy = ''
        for category in categories_list:
            hierarchy_list = category['hierarchy']
            category_names_list = []
            for hierarchy in hierarchy_list:
                category_names_list.append(hierarchy['displayName']['en'])
            category_hierarchy += '|'.join(category_names_list) + ', '

        product_data = {
            'sku': sku,
            'name': preloaded_json['entities']['skus'][sku]['name'],
            'package': preloaded_json['entities']['skus'][sku]['description'],
            'description': preloaded_json['entities']['skus'][sku]['longDescription'],
            'brand': preloaded_json['entities']['skus'][sku]['brand']['name'],
            'barcodes': ','.join(preloaded_json['entities']['skus'][sku]['upc']),
            'upc': preloaded_json['entities']['skus'][sku]['upc'][0], 'image_url': ','.join(image_urls),
            'category': category_hierarchy.rstrip(',')
        }
        yield product_data
