#-*-coding:utf8 -*-
import re
import multiprocessing
import pdb
import traceback
import codecs
from selenium import webdriver


class Config(object):
    '''配置文件类
    存放全局变量,通过Config方式调用
    '''
    url_path = 'url.txt'  #存放首页url文件
    img2l = './level2/img2.txt' #图片二级页面路径
    nov2l = './level2/nov2.txt' #小说二级页面路径
    vid2l = './level2/vid2.txt' #视频二级页面路径
    img3l = './level3/img3.txt' #图片3级页面路径
    nov3l = './level3/nov3.txt' #小说3级页面路径
    vid3l = './level3/vid3.txt' #视频3级页面路径

    process_num = 4 #进程池进程数量

    r_img2l = re.compile(u'.*(图片|图区|圖區).*') #图片二级页面的链接文本正则
    r_nov2l = re.compile(u'.*(小说|小說).*') #小说二级页面的链接文本正则
    r_vid2l = re.compile(u'.*(三级|电影|视频|快播|電影).*') #视频二级页面的链接文本正则
 
 
    l_img2l = multiprocessing.Manager().list() #存放2级图片链接,
    l_vid2l = multiprocessing.Manager().list() #存放2级视频链接
    l_nov2l = multiprocessing.Manager().list() #存放2级小说链接
    l_3l = multiprocessing.Manager().list() #存放3级链接


    encoding = 'utf8' #默认的网站页面编码

    #三级页面href编辑距离差值
    edit_dist = 3

    #匹配所有a链接正文
    #由于部分网站存在繁体字符,在用decode转换的时候繁体字符会消失故导致部分内容出错,例如99hphp
    #所以我们首先找到所有a链接的正文,然后再通过繁简转换,转换之后在判断是否有图片小说等关键字
    #r = re.compile(r'[\s\S]*?<a[\s\S]*?>([\s\S]*?)</a>[\s\S]*?')
    queue = [] #存放3级链接
    lock = multiprocessing.Lock()

class FileOper(object):
    '''文件操作类
    文件操作,读取文件,写入文件,根据值写入,根据数组写入等等
    '''
    def file_read(self,file_path):
        '''读取文件内容,返回一个数组'''
        result = []
        with open(file_path,'r') as f:
            for line in f.readlines():
                result.append(line.strip()) #首先过滤字符串前后空格
        return result

    def file_write(self,file_path,content):
        '''写入内容到某个文件中'''
        fw = codecs.open(file_path,'w','utf-8') #fw = open(file_path,'w')
        fw.write(content)
        fw.close()

    def file_writelines(self,file_path,lines):
        '''写入内容到某个文件中,此时的内容是一个数组
        注意:普通的write和writelines接口无法写入unicode字符,需要通过codecs的open函数写入
        '''
        try:
            fw = codecs.open(file_path,'w','utf-8') #fw = open(file_path,'w')
            fw.writelines(lines)
            fw.close()
        except:
            print 'error!:'
            print traceback.format_stack()
            pdb.set_trace() #调试使用
            fw.close()

def encode_conver(content):
    '''编码转换
    暂时只对gb2312,gbk和utf8编码,因为maxcms只有这两种编码,后续可扩充
    '''
    if content.find('gb') > -1:
        #无论是gb2312还是gbk同意用gbk进行解码
        content = content.decode('gbk','ignore')
    elif content.find('utf8') > -1:
        content = content.decode('utf8','ignore')
    else:
        content = content.decode('utf8','ignore')

    return content
