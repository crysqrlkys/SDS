from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_auth.registration.views import RegisterView
from rest_auth.views import LogoutView, LoginView

from donutsender.core import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'payments', views.PaymentViewSet)

auth_patterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('', include(auth_patterns)),

]
