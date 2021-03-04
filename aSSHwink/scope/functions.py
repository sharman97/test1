import cv2
import os
import math
import time
import numpy as np

from itertools import chain
import plotly.express as px
from plotly.offline import plot
import plotly.graph_objs as go

from django.shortcuts import render
from django.http import HttpResponse

#####Misc

sign = lambda x: int(math.copysign(1, x))


##### Camera and Light


def calcComplexity(img):
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=1)
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=1)
    return np.sum(sobelx ** 2 + sobely ** 2)


#############Image Viewer

def gen_thumb(name):
    if os.path.isfile("./scope/static/scope/snapshots/thumbs/" + name):
        return True
    else:
        print("Making new Thumb")
        img = cv2.imread("./scope/static/scope/snapshots/" + name)

        thumb = cv2.resize(img, (241, 188))
        return (cv2.imwrite("./scope/static/scope/snapshots/thumbs/" + name, thumb))


def handlePageContext(pageno, MAX_PAGE_NO):
    NO_OF_IDX = 6
    ANCHOR_IDX = 3
    if NO_OF_IDX > MAX_PAGE_NO:
        NO_OF_IDX = MAX_PAGE_NO
        ANCHOR_IDX = int(np.ceil(NO_OF_IDX / 2))

    allpageidx = []
    for i in range(1, MAX_PAGE_NO + 1):
        activity = ""
        if i == pageno:
            activity = "active"
        allpageidx.append({"pageno": i, "activity": activity})

    if (pageno - ANCHOR_IDX < 0):
        pageidx = allpageidx[0:NO_OF_IDX]
    elif (pageno + NO_OF_IDX - ANCHOR_IDX > MAX_PAGE_NO):
        pageidx = allpageidx[-NO_OF_IDX:]
    else:
        pageidx = allpageidx[pageno - ANCHOR_IDX:pageno + NO_OF_IDX - ANCHOR_IDX]

    page_prev = ""
    page_next = ""

    if pageno == 1:
        page_prev = "disabled"
    elif pageno == MAX_PAGE_NO:
        page_next = "disabled"
    if MAX_PAGE_NO == 1:
        page_next = "disabled"
        page_prev = "disabled"

    return {"pageidx": pageidx, "page_prev": page_prev, "page_next": page_next, "curr_page": pageno}


def rbc_plot(circles):
    radii = circles[0, :, 2]
    data = go.Histogram(x=radii)
    layout = go.Layout(
        title="RDW Plot",
        autosize=False,
        width=200,
        height=200,
        xaxis=go.layout.XAxis(linecolor='black',
                              linewidth=1),
        yaxis=go.layout.YAxis(linecolor='black',
                              linewidth=1),
        margin=go.layout.Margin(
            l=10,
            r=10,
            b=10,
            t=40,
            pad=1
        )
    )
    fig = go.Figure(data=data, layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    # print(plot_div)
    return plot_div


def circle_detect(params, name):
    param1 = params["param1"]
    param2 = params["param2"]
    minDist = params["minDist"]
    minRad = params["minRad"]
    maxRad = params["maxRad"]

    path = "./scope/static/scope/snapshots/" + name
    print(path)
    cimg = cv2.imread(path)
    img_mask, empty_cnt = empty_area_masking(cimg)
    img = cv2.cvtColor(cimg, cv2.COLOR_BGR2GRAY) * img_mask
    context = params
    context["name"] = name
    circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, minDist, param1=param1, param2=param2, minRadius=minRad,
                               maxRadius=maxRad)
    if circles is not None:
        circles = np.uint16(np.around(circles))

        for i in circles[0, :]:
            cv2.circle(cimg, (i[0], i[1]), i[2], [0, 0, 255], 2)
        plot_div = rbc_plot(circles)
        context["plot_div"] = plot_div
        context["rbc_count"] = len(circles[0, :, 2])

        context["rbc_conc"] = getRBCconc(context["rbc_count"], img_mask)

    path2 = "./scope/static/scope/rbc_detected/" + name

    cv2.drawContours(cimg, empty_cnt, -1, (255, 0, 0), -1)
    cv2.imwrite(path2, cimg)
    context["new_img"] = "/static/scope/rbc_detected/" + name
    context["old_img"] = "/static/scope/snapshots/" + name

    if "alert_message" not in context.keys():
        context["alert_disp_status"] = 'none'

    return context


def empty_area_masking(img):
    fimg = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    fimg = fimg[:, :, 2]
    fimg = abs(cv2.Laplacian(fimg, cv2.CV_32F))
    ret, fimg = cv2.threshold(fimg, 10, 255, cv2.THRESH_BINARY_INV)
    fimg = fimg.astype(np.uint8)
    k = 5
    fimg = cv2.medianBlur(fimg, k)
    k = 10
    ksize = np.ones((k, k), np.uint8)
    fimg = cv2.erode(fimg, ksize, iterations=1)
    k = 4
    ksize = (k, k)
    fimg = cv2.blur(fimg, ksize)
    ret, fimg = cv2.threshold(fimg, 100, 255, cv2.THRESH_BINARY)
    k = 15
    ksize = np.ones((k, k), np.uint8)
    fimg = cv2.dilate(fimg, ksize, iterations=1)
    k = 18
    ksize = np.ones((k, k), np.uint8)
    fimg = cv2.erode(fimg, ksize, iterations=1)
    k = 10
    ksize = np.ones((k, k), np.uint8)
    fimg = cv2.dilate(fimg, ksize, iterations=1)
    k = 31
    fimg = cv2.medianBlur(fimg, k)
    k = 60
    ksize = np.ones((k, k), np.uint8)
    fimg = cv2.morphologyEx(fimg, cv2.MORPH_CLOSE, ksize)
    fimg = fimg.astype(np.uint8)

    contours, hierarchy = cv2.findContours(fimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    kimg = fimg * 0
    cv2.drawContours(kimg, contours, -1, 255, -1)
    kimg = 255 - kimg
    return kimg, contours


def getRBCconc(count, mask):
    px = 1.4e-6  # pixel length
    height = 5e-6  # height of gap

    mag = 4.1755  # 5.37 ##magnification

    area = np.sum(mask) * px * px / 255.0

    conc = ((count * (mag ** 2)) / (area * height)) * 1e-15

    return round(conc, 2)

