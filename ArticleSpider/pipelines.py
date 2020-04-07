# -*- coding: utf-8 -*-
import codecs
import json

from scrapy.pipelines.images import ImagesPipeline
import MySQLdb
from twisted.enterprise import adbapi

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item

class MysqlPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect(host="192.168.1.200", user='root', passwd='root', db='article_spider', 
                    charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor()
    
    def process_item(self, item, spider):
        insert_sql = '''
            insert into cnblogs(title, url, url_object_id, front_image_url, front_image_path, praise_num, comment_num, fav_num, tags, content, create_date)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            on duplicate KEY update praise_num=VALUES(praise_num) 
        '''
        params = list()
        params.append(item.get('title', ''))
        params.append(item.get('url', ''))
        params.append(item.get('url_object_id', ''))
        front_image_list = ",".join(item.get('front_image_url', []))
        params.append(front_image_list)
        params.append(item.get('front_image_path', ''))
        params.append(item.get('praise_num', 0))
        params.append(item.get('comment_num', 0))
        params.append(item.get('fav_num', 0))
        params.append(item.get('tag', ''))
        params.append(item.get('content', ''))
        params.append(item.get('create_date', "1970-01-01"))
        self.cursor.execute(insert_sql, tuple(params))
        self.conn.commit()
        return item


class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        from MySQLdb.cursors import DictCursor
        dbparms = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        #使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider) #处理异常
        return item

    def handle_error(self, failure, item, spider):
        #处理异步插入的异常
        print (failure)

    def do_insert(self, cursor, item):

        insert_sql = '''
            insert into cnblogs(title, url, url_object_id, front_image_url, front_image_path, praise_num, comment_num, fav_num, tags, content, create_date)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            on duplicate KEY update praise_num=VALUES(praise_num) 
        '''
        params = list()
        params.append(item.get('title', ''))
        params.append(item.get('url', ''))
        params.append(item.get('url_object_id', ''))
        front_image_list = ",".join(item.get('front_image_url', []))
        params.append(front_image_list)
        params.append(item.get('front_image_path', ''))
        params.append(item.get('praise_num', 0))
        params.append(item.get('comment_num', 0))
        params.append(item.get('fav_num', 0))
        params.append(item.get('tag', ''))
        params.append(item.get('content', ''))
        params.append(item.get('create_date', "1970-01-01"))

        cursor.execute(insert_sql, tuple(params))


class JsonWithEncodingPipeline(object):
    # 自定义json文件导出
    def __init__(self):
        self.file = codecs.open('article.json', 'a', encoding='utf8')
    
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item

    def spider_closed(self):
        self.file.close()


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "front_image_url" in item:
            image_file_path = ""
            for ok, value in results:
                image_file_path = value["path"]
            item["front_image_path"] = image_file_path
        
        return item