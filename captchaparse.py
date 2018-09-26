import os
import cv2 as cv
import time
import numpy as np

def tempmatch(img, tmp): #返回相关值
    if img.shape[0] >= tmp.shape[0] and img.shape[1] >= tmp.shape[1]:
        method = eval('cv.TM_CCOEFF')
        res = cv.matchTemplate(img, tmp, method)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
        return max_val
    else:
        return 0

def get_captcha(img):
    if img is None:
        print('can not load img')
        sys.exit()
    
    list = []
    templates_path='D:/LearnCfromzero/python/captcha/split/templates'
    for template_name in os.listdir(templates_path):
            tmp = cv.imread(os.path.join(templates_path, template_name))
            
            list.append(tempmatch(img, tmp))
        #print(list)
    tmp_list=[name.split('.')[0] for name in os.listdir(templates_path)]
    tmp_dict = dict(zip(tmp_list, list))
        #print(tmp_dict)
    return sorted(tmp_dict, key=lambda x: tmp_dict[x])[-1] #输出相关值最大的字符


def binary_captchar(pathname):
    '''
    根据图片位置生成验证码
    '''

    img = cv.imread(pathname, 0)

    ret, dst = cv.threshold(img, 10, 255, cv.THRESH_BINARY) #二值化

    for i in range(img.shape[0]): #反色
        for j in range(img.shape[1]):
          dst[i,j]=255-dst[i,j]

    ret, labels = cv.connectedComponents(dst) #求连通区域

    unique, counts = np.unique(labels, return_counts=True)
    labels_counts = dict(zip(unique, counts)) #统计

    ret, bimg = cv.threshold(img, 127, 255, cv.THRESH_BINARY) #二值化底图

    for i in range(img.shape[0]):#降噪
        for j in range(img.shape[1]):
            if(labels_counts[labels[i, j]] < 10 or labels_counts[labels[i, j]] > 80):
                bimg[i, j] = 0
            else:
                bimg[i, j] = 255

    im2, contours, hierarchy = cv.findContours(bimg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    rects = [cv.minAreaRect(cnt) for cnt in contours] #每个轮廓取最小框

    #ch0 = img[rects[0]]

    boxes = [np.int0(cv.boxPoints(box)) for box in rects] #填充
    leftset = set()
    for box in boxes:
        leftset.add(min([i[0] for i in box]))
    left_list = sorted(leftset) #把识别出的字母部分从左向右排序

    captcha=''
    
    for left in left_list:
        for box in boxes:
            Xs = [i[0] for i in box]
            Ys = [i[1] for i in box]
            x1 = min(Xs)
            if(x1 != left):
                continue
            x2 = max(Xs)
            y1 = min(Ys)
            y2 = max(Ys)
            hight = y2 - y1
            width = x2 - x1
            crop = bimg[y1 - 1:y1 + hight + 2, x1 - 1:x1 + width + 2]   #切割成的小份
            
            tem_folder=os.path.join(os.path.abspath('.'), 'split')
            isExists = os.path.exists(tem_folder)
            if not isExists:
                os.makedirs(tem_folder)
                
            split_name = os.path.join(os.path.abspath('.'), 'split', str(time.time()) + '.png')
            #print(split_name)
            
            cv.imwrite(split_name, crop)
            split_img = cv.imread(split_name)
            '''
            if not split_img:
                print('can\' load split_img')
                sys.exit()
            '''
            

            '''
            写入之后再读取才可以
            '''
            captcha += get_captcha(split_img)
            

            os.remove(split_name) # 删除临时文件
            
    return captcha


if __name__ == '__main__':

    captcha_floder='D:\LearnCFromZero\python\captcha\captcha'
    for pathname in os.listdir(captcha_floder):
        if os.path.splitext(pathname)[-1] == '.png' or os.path.splitext(pathname)[-1] == '.jpg':
            print(binary_captchar(os.path.join(captcha_floder,pathname)))

    