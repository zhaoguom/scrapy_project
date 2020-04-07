# -*- coding: utf-8 -*-
from urllib import parse
import re
import json

import requests
import scrapy
from scrapy import Selector, Request

from ArticleSpider.items import CnblogsItem
from ArticleSpider.utils import common


class CnblogsSpider(scrapy.Spider):
    name = 'cnblogs'
    allowed_domains = ['news.cnblogs.com']
    start_urls = ['http://news.cnblogs.com/']

    def parse(self, response):
        '''
        1. 获取新闻列表页中的新闻url列表交给scrapy下载后调用相应的解析方法
        2. 获取下一页的url并交给scrapy进行下载，下载完成后交给parse继续跟进
        '''
        # url = response.xpath('//*[@id="entry_659072"]/div[2]/h2/a/@href').extract_first("")
        # url = response.xpath('//div[@id="news_list"]/div[1]/div[2]/h2/a/@href').extract_first("")
        # url = response.xpath('//div[@id="news_list"]//h2[@class="news_entry"]/a/@href').extract()
        # urls = response.css('#news_list h2 a::attr(href)').extract()
        # text = response.text
        # selector = Selector(text=text)
        # urls = selector.xpath('//div[@id="news_list"]//h2[@class="news_entry"]/a/@href').extract()

        # 获取新闻列表页中的新闻url列表交给scrapy处理
        post_nodes = response.xpath('//div[@class="news_block"]')
        for post_node in post_nodes:
            image_url = post_node.css(
                '.entry_summary a img::attr(src)').extract_first("")
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            post_url = post_node.css('h2 a::attr(href)').extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": image_url}, callback=self.parse_detail)

        # 提取下一页并交给scrapy处理
        # 通过xpath获取下一页
        # next_url = response.xpath("//a[contains(text(), 'Next >')]/@href").extract_first("")

        next_url = response.css(
            "div.pager a:last-child::text").extract_first("")
        if next_url == "Next >":
            next_url = response.css(
                "div.pager a:last-child::attr(href)").extract_first("")
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_detail(self, response):
        match_re = re.match(".*?(\d+)", response.url)
        if match_re:
            article_item = CnblogsItem()
            title = response.css('#news_title a::text').extract_first('')
            create_date = response.css('#news_info .time::text').extract_first()
            match_re_2 = re.match('.*?(\d+.*)', create_date)
            if match_re_2:
                create_date = match_re_2.group(1)
            content = response.css('#news_content').extract()[0]
            tag_list = response.css('.news_tags a::text').extract()
            tags = ",".join(tag_list)

            post_id = match_re.group(1)

            article_item['title'] = title
            article_item['create_date'] = create_date
            article_item['content'] = content
            article_item['tags'] = tags
            if response.meta.get("front_image_url", []):
                article_item['front_image_url'] = [response.meta.get('front_image_url', '')]
            article_item['url'] = response.url
            # html = requests.get(parse.urljoin(response.url, '/NewsAjax/GetAjaxNewsInfo?contentId={}'.format(post_id)))
            yield Request(url=parse.urljoin(response.url, '/NewsAjax/GetAjaxNewsInfo?contentId={}'.format(post_id)), 
                        meta = {"article_item": article_item}, callback=self.parse_nums)
            # j_data = json.loads(html.text)
            # praise_num = j_data.get('DiggCount')
            # fav_num = j_data.get('TotalView')
            # comment_num = j_data.get('CommentCount')

    def parse_nums(self, response):
        j_data = json.loads(response.text)
        article_item = response.meta.get('article_item', '')

        praise_num = j_data.get('DiggCount')
        fav_num = j_data.get('TotalView')
        comment_num = j_data.get('CommentCount')

        article_item['praise_num'] = praise_num
        article_item['fav_num'] = fav_num
        article_item['comment_num'] = comment_num
        article_item['url_object_id'] = common.get_md5(article_item['url'])

        yield article_item