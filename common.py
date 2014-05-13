#-*-coding:utf8 -*-
import re
import multiprocessing
import pdb
import traceback
import codecs
from selenium import webdriver




class FileOper(object):

    '''文件操作类
    文件操作,读取文件,写入文件,根据值写入,根据数组写入等等
    '''

    def file_read(self, file_path):
        '''读取文件内容,返回一个数组
        '''
        result = []
        with open(file_path, 'r') as f:
            for line in f.readlines():
                result.append(line.replace('\n','').strip())  # 首先过滤字符串前后空格
        return result

    def file_write(self, file_path, content):
        '''写入内容到某个文件中
        '''
        try:
            # 普通的write和writelines接口无法写入utf8,需要通过codecs的open函数写入
            fw = codecs.open(file_path, 'w', 'utf-8')
            fw.write(content)
            fw.close()
        except:
            print 'error!:'
            print traceback.format_stack()
            fw.close()

    def file_writelines(self, file_path, lines):
        '''写入内容到某个文件中,此时的内容是一个数组
        '''
        try:
            fw = codecs.open(file_path, 'w', 'utf-8')
            fw.writelines(lines)
            fw.close()
        except:
            print 'error!:'
            print traceback.format_stack()
            pdb.set_trace()  
            fw.close()


class BrowserList(object):

    """浏览器进程列表
    浏览器进程和app进程数量相同
    初始化参数:
        ch->chrome  
        ff->Firefox 
        pt->PhantomJS
    """

    def __init__(self, browser_name, process_num):
        super(BrowserList, self).__init__()
        self.queue = []
        self.browser_name = browser_name
        self.process_num = process_num
        
        for i in xrange(process_num):
            # webdriver.Firefox and webdriver.PhantomJS均可,PhantomJS是后台运行,效率高但是会出现部分页面乱码问题
            # todo:web.PhantomJS
            if browser_name is 'ch':
                self.queue.append(webdriver.Chrome())
            elif browser_name is 'ff':
                self.queue.append(webdriver.Firefox())
            elif browser_name is 'ptm':
                self.queue.append(webdriver.PhantomJS())
            else:
                self.queue.append(webdriver.Chrome())

    def close_browser(self):
        '''关闭浏览器进程
        '''
        for i in xrange(self.process_num):
            self.queue[i].quit()

    def get_browser(self):
        '''获取空闲的浏览器进程
        '''

        for i in xrange(self.process_num):
            # Firefox & PhantomJS 默认地址和Chrome 不同
            # if Config.queue[i].current_url == 'about:blank':
            # Chrome默认地址
            if self.browser_name is 'ch':
                # 进程空闲
                if self.queue[i].current_url == 'data:,':
                    ptm = self.queue[i]  # 将browser进程放到Manager中会导致出现错误,故存放到数组中
                    break
            elif self.browser_name is 'ff':
                # 进程空闲
                if self.queue[i].current_url == 'about:blank':
                    ptm = self.queue[i]
                    break
            elif self.browser_name is 'ptm':
                # 进程空闲
                if self.queue[i].current_url == 'about:blank':
                    ptm = self.queue[i]
                    break
            else:
                # 进程空闲
                if self.queue[i].current_url == 'data:,':
                    ptm = Config.queue[i]
                    break

        # 成功获取浏览器进程,某些情况下浏览器进程异常会导致退出进程,故需要重新分配
        return ptm

class Config(object):

    '''配置文件类
    存放全局变量,通过Config方式调用
    '''
    url_path = 'url.txt'         # 存放待采集网站的首页地址

    img2l = './level2/img2.txt'  # 存放图片2级页面url
    nov2l = './level2/nov2.txt'  # 存放小说2级页面url
    vid2l = './level2/vid2.txt'  # 存放视频2级页面url
    img3l = './level3/img3.txt'  # 存放图片3级页面url
    nov3l = './level3/nov3.txt'  # 存放小说3级页面url
    vid3l = './level3/vid3.txt'  # 存放视频3级页面url

    process_num = 2  # 进程数量,可根据cpu数量选择,一般cpu数量*2即可

    # 已下4个变量是整个url采集工具的"参数"部分,可动态调整和配置
    r_img2l = re.compile(u'.*(图片|图区|圖區).*')      # 图片二级页面的链接文本正则
    r_nov2l = re.compile(u'.*(小说|小說).*')          # 小说二级页面的链接文本正则
    r_vid2l = re.compile(u'.*(电影|视频|快播|電影).*')  # 视频二级页面的链接文本正则
    edit_dist = 3  # 三级页面href编辑距离差值的benchmark(此值可优化,数值越大则越容易抽取错误链接)

    # 进程间共享数据
    lock = multiprocessing.Lock()  # 进程锁,保证浏览器进程和app进程数量相同
    l_img2l = multiprocessing.Manager().list()  # 存放2级图片链接
    l_vid2l = multiprocessing.Manager().list()  # 存放2级视频链接
    l_nov2l = multiprocessing.Manager().list()  # 存放2级小说链接
    l_3l = multiprocessing.Manager().list()     # 存放3级链接(可通用)

    # 初始化浏览器列表
    browser_list = BrowserList('ch',process_num)
