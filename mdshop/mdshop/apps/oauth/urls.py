from django.conf.urls import url

from oauth import views

urlpatterns = [
    url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
    url(r'^qq/user/$', views.QQAuthView.as_view()),
]