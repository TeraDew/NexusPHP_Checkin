import os
import cv2 as cv
import time
import numpy as np


def binary_captchar(pathname):
    img = cv.imread(os.path.join(os.path.abspath('.'), 'captcha',pathname), 0)

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
    
    cv.imwrite(os.path.join(os.path.abspath('.'), 'captcha','binary',('binary_' + pathname)), bimg)

    im2, contours, hierarchy = cv.findContours(bimg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    rects = [cv.minAreaRect(cnt) for cnt in contours] #每个轮廓取最小框

    boxes = [np.int0(cv.boxPoints(box)) for box in rects] #填充

    for box in boxes:
        Xs = [i[0] for i in box]
        Ys = [i[1] for i in box]
        x1 = min(Xs)
        x2 = max(Xs)
        y1 = min(Ys)
        y2 = max(Ys)
        hight = y2 - y1
        width = x2 - x1
        crop =  bimg[y1 - 1:y1 + hight + 2, x1 - 1:x1 + width + 2]
        cv.imwrite(os.path.join(os.path.abspath('.'), 'captcha',(str(time.time())+'.png'),crop)
    
for pathname in os.listdir(os.path.join(os.path.abspath('.'), 'captcha')):
    if pathname.split('.')[-1]=='png' or pathname.split('.')[-1]=='jpg':
        binary_captchar(pathname)