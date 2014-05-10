#coding:utf8
line_num = [1,-2,3,-1,5,6,7,-5,6,-4,1,1,1]

def get_max_idx(mylist):
    '''获取最大值对应的索引
    '''
    maxmium = 0
    max_idx = 0
    for idx,value in enumerate(mylist):
        if value > maxmium:
            max_idx = idx
            maxmium = value
    return max_idx

def get_max_sum_list():
    ''' 获取每一个元素的连续子序列最大值
    状态:是否包含当前值
    状态转移方程  f(n) = max(f(n-1)+a[n],a[n])
    '''
    a=line_num
    my_len = len(a)
    sum_list = [a[0]]*my_len
    for idx,v in enumerate(a[1:]):
        sum_list[idx+1] =  max([sum_list[idx]+a[idx+1],a[idx+1]])

    return sum_list

def get_scope():
    '''
    根据获取到的最大值获取最终在文档中的范围位置
    '''
    #获取最大值对应的索引
    mylist = get_max_sum_list()
    myidx = get_max_idx(mylist)
    maxmium = max(mylist)
    mysum = 0
    my_new_list = line_num[0:myidx+1]
    #print '每个元素最大值数组:{0}'.format(mylist)
    #print '最大值对应的索引:{0}'.format(myidx)
    #print '最大值:{0}'.format(maxmium)
    for value in xrange(len(my_new_list)):
        minus_value = myidx-value
        new_list =  my_new_list[minus_value:]
        if sum(new_list) == maxmium:
            #print '范围是(索引从0开始,对应到原文需+1):[{0},{1}]'.format(myidx-value,myidx)
            #print line_num[myidx-value:myidx+1]
            break;
    return myidx-value,myidx

if __name__ == "__main__":
    get_scope()
