from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.template import Context, Template
from django.shortcuts import redirect
from django.views.decorators import gzip

import glob
import os
import threading

from scope.camera import *
from scope.lights import *
from scope.rbc_detection import *
from scope.models import *
from scope.stepper import *

from scope.functions import *

# Setup Lights
illum = Lights()

# Setup Motors
MAXPOSX = 20000
MAXPOSY = 20000
MAXPOSZ = 12000
Mz = Motor("Mz", channel=[31, 33, 35, 37], maxpos=MAXPOSZ)
Mx = Motor("Mx", channel=[18, 22, 24, 26], maxpos=MAXPOSX)
My = Motor("My", channel=[32, 36, 38, 40], maxpos=MAXPOSY)

# sSetup Camera
scope = ScopeStream(set_fps=30, quality=60, resolution=(688, 480))


# Requests


@gzip.gzip_page
def stream(request):
    return StreamingHttpResponse(scope.start_stream_object(), content_type="multipart/x-mixed-replace;boundary=frame")


def index(request):
    return (render(request, 'index.html'))


def snap(request):
    print("Snapping bitc")
    scope.capture_still()
    return HttpResponse(0)


def light(request, action):
    print(action)
    if action != 'bf':
        illum.df(action)
    else:
        illum.bf()
    return HttpResponse(0)


def move(request, action, bigstep=0):
    if action in ['u', 'd', 'r', 'l']:
        if bigstep == 1:
            movestep = 500
        else:
            movestep = 100
    elif action in ['f', 'df']:
        if bigstep == 1:
            movestep = 200
        else:
            movestep = 20

    if action == 'u':
        ret = My.move(movestep, 1)
    elif action == 'd':
        ret = My.move(movestep, -1)
    elif action == 'r':
        ret = Mx.move(movestep, -1)
    elif action == 'l':
        ret = Mx.move(movestep, 1)
    elif action == 'f':
        ret = Mz.move(movestep, -1)
        print(calcComplexity(scope.img))
    elif action == 'df':
        ret = Mz.move(movestep, 1)
        print(calcComplexity(scope.img))
    else:
        ret = "Invalid action"

    return HttpResponse(ret)


def reset_max_motors(request):
    Mx.reset_max()
    My.reset_max()
    Mz.reset_max()
    return HttpResponse("Motors reset")


def autofocus(request):
    stepsize = 200
    diff = 100000000000
    old_cmplx = calcComplexity(scope.img)
    while abs(diff) > 100000 and abs(stepsize) > 5:

        print("mvoing:", int(abs(stepsize)), sign(stepsize))
        Mz.move(int(abs(stepsize)), sign(stepsize))
        new_cmplx = calcComplexity(scope.img)
        diff = new_cmplx - old_cmplx
        old_cmplx = new_cmplx.copy()

        print("complexity:", new_cmplx, diff)
        if diff > 0:
            stepsize = stepsize * 0.3
        else:
            stepsize = -stepsize * 1.2
        # if abs(stepsize)<5:
        #    stepsize=sign(stepsize)*5
    return HttpResponse(0)


def img_viewer(request, pageno=1):
    IMGS_PER_PAGE = 12

    files = glob.glob("./scope/static/scope/snapshots/*.jpg")
    files.sort(key=os.path.getmtime, reverse=True)
    names = [os.path.basename(path) for path in files]
    # names = [files for root, dirs, files in os.walk("./scope/static/scope/snapshots/")][0]
    # names = sorted(names, reverse=True)

    # names=files
    MAX_PAGE_NO = int(len(names) / IMGS_PER_PAGE) + 1
    if (pageno > MAX_PAGE_NO):
        return HttpResponseNotFound("Page not found")

    context = handlePageContext(pageno, MAX_PAGE_NO)

    names = names[IMGS_PER_PAGE * (pageno - 1):IMGS_PER_PAGE * (pageno)]

    imgs = []
    for nam in names:
        if nam[-2:] != '.0':
            gen_thumb(nam)
            path = "/scope/snapshots/" + nam
            thumbpath = "/scope/snapshots/thumbs/" + nam
            tim = int(nam.split('_')[-1][:-4])
            print(tim)
            date = time.strftime('%d-%m-%Y', time.localtime(int(tim)))
            ntim = time.strftime('%H:%M:%S', time.localtime(int(tim)))
            img = {'path': path, 'time': ntim, 'date': date, 'name': nam, 'thumbpath': thumbpath}
            imgs.append(img)

    context['imgs'] = imgs

    # {"nums":range(1,len(names)+1),"filenames":names,"paths":paths,"dates":dates,"times":time  }
    return (render(request, 'img_viewer.html', context))


def del_img(request, name):
    os.remove("./scope/static/scope/snapshots/thumbs/" + name)
    os.remove("./scope/static/scope/snapshots/" + name)
    return HttpResponse("Deleted" + name)


def rbc_snap_detector(request, name):
    default_params = RBCDetectParams.objects.get(pk=1).asdict()

    if request.method == 'POST':
        form = RBCDetectForm(request.POST)
        if form.is_valid():
            params = form.cleaned_data
            context = circle_detect(params, name)
            return (render(request, 'rbc_snap_detect.html', context))
        else:
            params = default_params
            params["alert_message"] = "Invalid Input Value"
            context = circle_detect(params, name)
            return (render(request, 'rbc_snap_detect.html', context))
    else:
        params = default_params
        context = circle_detect(default_params, name)
        return (render(request, 'rbc_snap_detect.html', context))


def set_default_RBC_params(request):
    default_params = RBCDetectParams.objects.get(pk=1)

    if request.method == 'POST':
        form = RBCDetectForm(request.POST)
        if form.is_valid():
            params = form.cleaned_data
            default_params.updatedict(params)
            default_params.save()
            return HttpResponse(status=204)
        else:
            return HttpResponse("Invalid Defaults")
    else:
        return HttpResponse("Why are you here young lad?")


manual_rbc_count = 1
rbc_detect_paths = []#"snap_1599392693.jpg","snap_1599392609.jpg","snap_1599392480.jpg","snap_1599392426.jpg","snap_1599392399.jpg"]
report_samples=[]
NO_RBC_PICS = 3


def rbc_detect(request):
    global manual_rbc_count, rbc_detect_paths
    rbc_detect_paths = []
    manual_rbc_count = 1
    return (render(request, 'rbc_detect.html'))


def manual_rbc_snap(request):
    global manual_rbc_count, rbc_detect_paths
    det_time = str(int(time.time()))
    filename = "rbc_det_" + str(manual_rbc_count) + "_" + det_time + ".jpg"
    scope.capture_still(filename)
    rbc_detect_paths.append(filename)
    while (scope.still_cap):
        pass
    manual_rbc_count += 1

    if manual_rbc_count > NO_RBC_PICS:

        return HttpResponse("show_report")

    return HttpResponse("Image Registered " + str(manual_rbc_count - 1))


def show_rbc_report(request):
    global manual_rbc_count, rbc_detect_paths,report_samples

    print("Showing Report")
    default_params = RBCDetectParams.objects.get(pk=1).asdict()

    conc=[]
    threads=[]
    for path in rbc_detect_paths:
        print("Processing", path)
        t= threading.Thread(target=threaded_cir_det, args=(default_params, path,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    samples=report_samples.copy()
    try:
        for sample in samples:
            conc.append(sample["rbc_conc"])
        conc=round(np.average(conc),2)
    except:
        pass
    message="Normal range is 4-6 M/uL"
    context = {"samples": samples,"rbc_conc":conc,"message":message}
    rbc_detect_paths = []
    report_samples=[]
    manual_rbc_count = 1
    return (render(request, 'rbc_report.html', context))

def threaded_cir_det(default_params, path):
    global report_samples
    cont=circle_detect(default_params, path)
    with threading.Lock():
        report_samples.append(cont.copy())
        time.sleep(0.1)


def rbc_auto(request):
    global rbc_detect_paths
    rbc_detect_paths = []
    det_time = str(int(time.time()))
    steps=[ [[4500,1],[2000,1]],
            [[4500, 1], [2000, 1]],
            [[9000, -1], [4000, -1]],
        ]
    for i in range(NO_RBC_PICS):
        filename = "rbc_det_" + str(i) + "_" + det_time + ".jpg"
        scope.capture_still(filename)
        while (scope.still_cap):
            pass
        rbc_detect_paths.append(filename)
        t1 = threading.Thread(target=My.move, args=(steps[i][0][0], steps[i][0][1],))
        t2 = threading.Thread(target=Mx.move, args=(steps[i][1][0], steps[i][1][1],))
        t1.start()
        t2.start()

        if i <NO_RBC_PICS-1:
            t1.join()
            t2.join()

    return HttpResponse("show_report")

