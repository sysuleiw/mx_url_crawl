#-*-coding:utf8 -*-
from BeautifulSoup import BeautifulSoup #http://www.leeon.me/upload/other/beautifulsoup-documentation-zh.html
import os
import time #计算运行时间
import multiprocessing
from common import *
import get_scope
import urlparse
from Levenshtein import *
import re
import traceback
import requests
from selenium import webdriver

'''目前有一下几类站点采集不到
一.首页到二级
1.通过js跳转的 ggg43.com
2.部分页面内容是通过js动态生成  atv234.com
3.没有导航链接,例如88gugu.com
4.部分页面部分导航是js生成,例如kk3xx,电影区的一栏是通过js生成的

二.二级到三级
1.前提是二级列表链接的url编辑距离相差较少
'''
'''
brew install chromedriver 需要独立安装
'''

def init_browser():
    '''创建浏览器进程'''
    for i in xrange(Config.process_num):
        Config.queue.append(webdriver.Chrome())

def close_browser():
    for i in xrange(Config.process_num):
        Config.queue[i].quit()

def get_browser():
    '''将browser进程放到Manager共享内存中会导致出现错误
    '''
    for i in xrange(Config.process_num):
        #Firefox默认地址
        #if Config.queue[i].current_url == 'about:blank':
        #Chrome默认地址
        if Config.queue[i].current_url == 'data:,':
            ptm = Config.queue[i]
    return ptm

def parse2l(url):
    '''2级页面进程池目标函数
    二级url查找办法:
    1.找到页面所有a链接并记录所有a链接的textContent长度
    2.长度相同则记录1,否则记录为-1,支持如果有n个a,则有n-1个1和-1组成的序列,然后存放到数组中
    3.利用求最长公共子序列和的方法求解范围
    4.根据范围找到对应的a链接范围
    5.找到图片/电影|快播|视频/图片关键字
    6.从上面找到的每一个链接后面的链接,至此找到最终的二级页面url
    '''

    #print 'url:{0}  pid{1}'.format(url,os.getpid())
    b_add_img = 0 #判断图片2级是否已添加
    b_add_vid = 0 #判断视频级是否已添加
    b_add_nov = 0 #判断小说2级是否已添加
    img2l_link ='' #存储找到第一个符合标准的图片链接
    nov2l_link ='' #存储找到第一个符合标准的图片链接
    vid2l_link ='' #存储找到第一个符合标准的图片链接
    print 'url:' + url
    #需要添加同步锁,防止第一次运行出现同时获取到第一个browser
    Config.lock.acquire()
    #if len(Config.queue):
    #    ptm = Config.queue.pop()
    ptm = get_browser()
    ##ptm = Config.queue.get()
    Config.lock.release()
    #ptm = webdriver.Firefox()
    try:
        #r = requests.get(url)
        ptm.get(url)
        #r.encoding是用来decode r.text的编码格式 r.apparent_encoding: 获取文档的实际编码
        #r.encoding = r.apparent_encoding.lower().find('gb') > -1 and 'gbk' or 'utf8'  
        #soup = BeautifulSoup(r.text) #以此构建dom树
        #统计所有a链接与前一个链接的文本数量差
        list_a = ptm.find_elements_by_tag_name('a') 
        last_len = 0 #初始化0
        result = []
        for a in list_a:
            if (len(a.text.strip()) - last_len) == 0:
                result.append(1)           
            else:
                result.append(-1)           
            #保留上一个a链接
            last_len = len(a.text.strip())

        #
        if len(result):
            #获取最大连续和
            get_scope.line_num = result
            start,end = get_scope.get_scope()
            #通过关键字寻找对应的图片,小说,电影链接
            for idx in xrange(end+1):
                if len(Config.r_img2l.findall(list_a[idx].text)) and not b_add_img:
                    img2l_link = list_a[idx+2]
                    img2l_url = urlparse.urljoin(url,img2l_link.get_attribute('href')) + '\n'
                    #urlparse 对于urlparse.urljoin('http://www.333rv.com','../vodlist/2.html'无法得到正确结果
                    img2l_url = img2l_url.replace('../','')
                    Config.l_img2l.append(img2l_url)
                    b_add_img = True
                elif len(Config.r_nov2l.findall(list_a[idx].text)) and not b_add_nov:
                    #找到图片头
                    nov2l_link = list_a[idx+2]
                    nov2l_url = urlparse.urljoin(url,nov2l_link.get_attribute('href')) + '\n'
                    nov2l_url = nov2l_url.replace('../','')
                    Config.l_nov2l.append(nov2l_url)
                    b_add_nov = True
                elif len(Config.r_vid2l.findall(list_a[idx].text)) and not b_add_vid:
                    #找到图片头
                    vid2l_link = list_a[idx+2]
                    vid2l_url = urlparse.urljoin(url,vid2l_link.get_attribute('href')) + '\n'
                    vid2l_url = vid2l_url.replace('../','')
                    Config.l_vid2l.append(vid2l_url)
                    b_add_vid = True
                    #打印相关信息
            #print url
            #print Config.l_img2l[0] + '   ' + img2l_link.text
            #print Config.l_nov2l[0] + '   ' + nov2l_link.text
            #print Config.l_vid2l[0] + '   ' + vid2l_link.text
        ptm.get('data:,')
    except Exception,e:
        print '2lerror:' + url
        print e
        print traceback.format_exc()

def get_302_url(content):
    '''获取302跳转之后的页面内容
    1.通过meta refresh跳转
    2.通过location.replace跳转,如location.replace("http://www.400ks.com/avlist/1.html")

    主要通过分析页面内容查找对应的url然后进行二次抓取
    '''
    r_meta = re.compile(r'.*content=[\s\S]*url=(.*?)">') 
    r_js = re.compile(r'.*location.replace\("(.*?)"\).*') 
    r_list = []
    r_list.append(r_meta)
    r_list.append(r_js)

    for r in r_list:
        mylist = r.findall(content)
        if len(mylist):
            return mylist[0]

    return ''


def parse3l(url):
    '''三级页面url获取方式
    1.遍历页面所有a连接
    2.计算当前链接和上一个链接的href的编辑距离差,思路同上面一个步骤的相同,编辑距离差小于2存成1,否则存成-1
    3.利用最长序列和算法找出对应的链接范围,然后从其中取出来一个即可
    '''
    Config.lock.acquire()
    #if len(Config.queue):
    #    ptm = Config.queue.pop()
    ptm = get_browser()
    ##ptm = Config.queue.get()
    Config.lock.release()
    #ptm = webdriver.Firefox()
    #if len(Config.queue):
    #    ptm = Config.queue.pop()
    #ptm = Config.queue.get()
    #ptm = webdriver.Firefox()
    ptm.get(url)
    #r = requests.get(url)
    #r.encoding = r.apparent_encoding.lower().find('gb') > -1 and 'gbk' or 'utf8'  
    #soup = BeautifulSoup(r.text) #以此构建dom树
    list_a = ptm.find_elements_by_tag_name('a') 
    #list_a = soup('a') 
    last = '' #初始化0
    result = []
    print '3lurl:' + url
    try:
        for a in list_a:
            if a.get_attribute('href'):
                try:
                    #href可能包含中文,因此捕获异常
                    if distance(str(a.get_attribute('href').strip()) , str(last)) < Config.edit_dist:
                        result.append(1)           
                    else:
                        result.append(-1)           
                    #保留上一个a链接
                    last = a.get_attribute('href').strip() 
                except:
                    print '3l_unicode_error:' + a.get_attribute('href')

        if len(result):
            print '3lurl3:' + url
            get_scope.line_num = result
            start,end = get_scope.get_scope()
            middle = (end-start)/2 + start
            print '3lurl4:' + url
            while middle:
                if list_a[middle].get_attribute('href'):
                    Config.l_3l.append(urlparse.urljoin(url,list_a[middle].get_attribute('href')) + '\n')
                    break
                else:
                    middle -= 1
        else:
            #有可能是该网页出现302跳转,故没有a连接
            url2 = get_302_url(r.text)
            print '没找到链接url:' + url +':url2:' + url2
            if url2:
                parse3l(url2)
        ptm.get('data:,')
    except Exception,e:
        print '3lerror:' + url
        print e
        print traceback.format_exc()

class Spider(object):
    '''url获取器
    根据首页相关的url获取对应网站下的二级和三级页面的url
    '''
    fileoper = FileOper()
        
    def get2l_url(self):
        url_list = map(lambda url: 'http://' +  url,self.fileoper.file_read(Config.url_path)) 
        pool = multiprocessing.Pool(Config.process_num)
        pool.map(parse2l,url_list) #这里的数组在进程池中不是按顺序访问
        #分别写入到对应的文件中
        self.fileoper.file_writelines(Config.img2l,Config.l_img2l)
        self.fileoper.file_writelines(Config.nov2l,Config.l_nov2l)
        self.fileoper.file_writelines(Config.vid2l,Config.l_vid2l)

    def get3l_url(self):
        l2_path = [Config.img2l,Config.nov2l,Config.vid2l]
        l3_path = [Config.img3l,Config.nov3l,Config.vid3l]
        for idx,path in enumerate(l2_path):
            url_list = self.fileoper.file_read(path)
            pool = multiprocessing.Pool(Config.process_num)
            pool.map(parse3l,url_list) #这里的数组在进程池中不是按顺序访问
            self.fileoper.file_writelines(l3_path[idx],Config.l_3l)
            Config.l_3l = multiprocessing.Manager().list() #存放3级链接

if __name__ == "__main__":
    init_browser()
    spider = Spider()
    start = time.time()
    spider.get2l_url()#抓取2级页面
    spider.get3l_url()#抓取3级页面
    finish = time.time()
    close_browser()
    print 'elapse time:{0}'.format(finish-start)
