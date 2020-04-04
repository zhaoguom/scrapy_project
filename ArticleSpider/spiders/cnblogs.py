# -*- coding: utf-8 -*-
import scrapy
from scrapy import Selector


class CnblogsSpider(scrapy.Spider):
    name = 'cnblogs'
    allowed_domains = ['news.cnblogs.com']
    start_urls = ['http://news.cnblogs.com/']

    def parse(self, response):
        # url = response.xpath('//*[@id="entry_659072"]/div[2]/h2/a/@href').extract_first("")
        # url = response.xpath('//div[@id="news_list"]/div[1]/div[2]/h2/a/@href').extract_first("")
        url = response.xpath('//div[@id="news_list"]//h2[@class="news_entry"]/a/@href').extract()
        # urls = response.css('#news_list h2 a::attr(href)').extract()
        # text = response.text
        # selector = Selector(text=text)
        # urls = selector.xpath('//div[@id="news_list"]//h2[@class="news_entry"]/a/@href').extract()
        pass
