from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_auth.registration.views import RegisterView
from rest_auth.views import LogoutView, LoginView

from donutsender.core import views

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet)
router.register(r'donate', views.PaymentViewSet)
router.register(r'd', views.PaymentPageViewSet)
router.register(r'withdraw', views.WithdrawalViewSet)
router.register(r'settings', views.SettingsViewSet)

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
