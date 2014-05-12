# coding:utf8
import time
from spider import Spider


if __name__ == "__main__":
    spider = Spider()
    start = time.time()
    spider.get2l_url()  # 抓取2级页面
    spider.get3l_url()  # 抓取3级页面
    finish = time.time()
    spider.close_browser()  # 关闭所有浏览器进程

    print 'elapse time:{0}'.format(finish - start)
