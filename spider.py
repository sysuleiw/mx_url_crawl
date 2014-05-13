#-*-coding:utf8 -*-
import multiprocessing
import traceback
import get_max_sum
import urlparse
from Levenshtein import *  # 求解编辑距离,利用动态规划算法,已有现成包可用
from common import *


def get_2l_by_text(start, end, a_list, url):
    '''通过给定的a链接范围查找对应的链接
    '''
    b_add_img = 0  # 判断图片2级是否已添加
    b_add_vid = 0  # 判断视频级是否已添加
    b_add_nov = 0  # 判断小说2级是否已添加
    img2l_link = ''  # 存储找到第一个符合标准的图片链接
    nov2l_link = ''  # 存储找到第一个符合标准的图片链接
    vid2l_link = ''  # 存储找到第一个符合标准的图片链接
    # a_list[start:end] 部分站点的分类链接是3个字,会导致计算文字距离差的时候出现-1值,后期考虑到性能优化可更改start参数
    list_a = a_list[0:end]
    # 通过关键字寻找对应的图片,小说,电影链接
    for idx, value in enumerate(list_a):
        if len(Config.r_img2l.findall(list_a[idx].text)) and not b_add_img:
            img2l_link = list_a[idx + 2]
            # 对于urlparse.urljoin('http://www.333rv.com','../vodlist/2.html'无法得到正确结果,原因是原网站url错误
            img2l_url = urlparse.urljoin(
                url, img2l_link.get_attribute('href')).replace('../', '') + '\n'
            Config.l_img2l.append(img2l_url)
            b_add_img = True
        elif len(Config.r_nov2l.findall(list_a[idx].text)) and not b_add_nov:
            # 找到图片头
            nov2l_link = list_a[idx + 2]
            nov2l_url = urlparse.urljoin(
                url, nov2l_link.get_attribute('href')).replace('../', '') + '\n'
            Config.l_nov2l.append(nov2l_url)
            b_add_nov = True
        elif len(Config.r_vid2l.findall(list_a[idx].text)) and not b_add_vid:
            # 找到图片头
            vid2l_link = list_a[idx + 2]
            vid2l_url = urlparse.urljoin(
                url, vid2l_link.get_attribute('href')).replace('../', '') + '\n'
            Config.l_vid2l.append(vid2l_url)
            b_add_vid = True


def parse2l(url):
    '''2级页面进程池目标函数
    '''
    # 需要添加同步锁,防止第一次运行出现同时获取到第一个browser,影响效率
    Config.lock.acquire()
    ptm = Config.browser_list.get_browser()
    Config.lock.release()

    # print 'url:{0}  pid{1}'.format(url,os.getpid())

    try:
        ptm.get(url)
        # 统计所有a链接与前一个链接的文本数量差
        list_a = ptm.find_elements_by_tag_name('a')
        last_len = 0  # 初始化0
        result = []
        for a in list_a:
            cur_len = len(a.text.strip())
            if cur_len - last_len == 0:
                result.append(1)
            else:
                result.append(-1)
            # 保留当前链接文本长度
            last_len = cur_len

        if len(result):
            # 获取最大连续和
            start, end = get_max_sum.main(result)
            get_2l_by_text(start, end, list_a, url)
        # 执行完毕后设置浏览器为空闲状态
        ptm.get('data:,')
    except Exception, e:
        print '2lerror:' + url
        print e
        print traceback.format_exc()


def parse3l(url):
    '''三级页面url获取方式
    '''

    Config.lock.acquire()
    ptm = Config.browser_list.get_browser()
    Config.lock.release()

    ptm.get(url)

    list_a = ptm.find_elements_by_tag_name('a')
    last = ''  # 初始化0
    last_txt = ''
    result = []
    try:
        for a in list_a:
            if a.get_attribute('href'):
                try:
                    # href可能包含中文,因此捕获异常
                    # 编辑距离小于3并且两个链接的字数不能相等(过滤导航,部分站点导航的href差异很小,需要通过文本数量过滤)
                    if (distance(str(a.get_attribute('href').strip()), str(last)) < Config.edit_dist) and \
                        len(a.text.strip()) - len(last_txt) != 0:
                        result.append(1)
                    else:
                        result.append(-1)
                    # 保留上一个a链接
                    last = a.get_attribute('href').strip()
                    last_txt = a.text.strip()
                except:
                    print '3l_unicode_error:' + a.get_attribute('href')
        if len(result):
            start, end = get_max_sum.main(result)
            middle = (end - start) / 2 + start
            while middle:
                href = list_a[middle].get_attribute('href')
                if href:
                    href = urlparse.urljoin(
                        url, href).replace('../', '') + '\n'
                    Config.l_3l.append(href)
                    break
                else:
                    middle -= 1
        ptm.get('data:,')
    except Exception, e:
        print '3lerror:' + url
        print e
        print traceback.format_exc()


class Spider(object):

    '''url获取器
    根据首页相关的url获取对应网站下的二级和三级页面的url
    '''

    def __init__(self):
        super(Spider, self).__init__()
        self.fileoper = FileOper()

    def get2l_url(self):
        '''获取2级页面url地址
        '''
        url_list = map(lambda url: 'http://' + url,
                       self.fileoper.file_read(Config.url_path))
        pool = multiprocessing.Pool(Config.process_num)
        pool.map(parse2l, url_list)  # 这里的数组在进程池中不是按顺序访问
        # 分别写入到对应的文件中
        self.fileoper.file_writelines(Config.img2l, Config.l_img2l)
        self.fileoper.file_writelines(Config.nov2l, Config.l_nov2l)
        self.fileoper.file_writelines(Config.vid2l, Config.l_vid2l)

    def get3l_url(self):
        '''获取3级页面url地址
        '''
        l2_path = [Config.img2l, Config.nov2l, Config.vid2l]
        l3_path = [Config.img3l, Config.nov3l, Config.vid3l]

        for idx, path in enumerate(l2_path):
            url_list = self.fileoper.file_read(path)
            pool = multiprocessing.Pool(Config.process_num)
            pool.map(parse3l, url_list)  # 这里的数组在进程池中不是按顺序访问
            self.fileoper.file_writelines(l3_path[idx], Config.l_3l)
            Config.l_3l = multiprocessing.Manager().list()  # 清空3级链接共享内存

    def close_browser(self):
        '''调用结束关闭浏览器进程
        '''
        try:
            Config.browser_list.close_browser()
        except:
            print 'close_browser error!'
            pass
