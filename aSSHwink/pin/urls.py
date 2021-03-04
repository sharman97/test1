from django.urls import path
from . import views

urlpatterns = [
path('',views.pinAuth,name='pinAuth'),
path('auth/',views.auth,name='auth'),
path('<int:pin_sent>/',views.autoPinAuth,name='autoPinAuth'),
]