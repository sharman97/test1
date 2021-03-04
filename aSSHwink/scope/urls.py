from django.urls import path
from . import views

urlpatterns = [
path('stream/',views.stream,name='stream'),
path('snap/',views.snap,name='snap'),
path('af/',views.autofocus,name='autofocus'),
path('move/<str:action>/<int:bigstep>',views.move,name='move'),
path('move/reset_max',views.reset_max_motors),
path('light/<str:action>/',views.light,name='light'),
path('img_viewer/<int:pageno>',views.img_viewer,name='img_viewer'),
path('delete/<str:name>/',views.del_img,name='delete'),
path('rbc_snap_detect/form/<str:name>/',views.rbc_snap_detector,name='rbcform'),
path('rbc_snap_detect/update_default/', views.set_default_RBC_params, name='update_rbc_params'),
path('rbc_detect/',views.rbc_detect,name='rbc_detect'),
path('rbc_detect/manual_snap/',views.manual_rbc_snap,name='manual_snap'),
path('rbc_detect/auto/',views.rbc_auto,name='rbc_auto'),
path('rbc_detect/report/',views.show_rbc_report,name='rbc_report'),
path('',views.index,name='index')
]