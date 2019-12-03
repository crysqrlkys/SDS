from django.contrib import admin

from donutsender.core.models import User, Notifications, Payment

admin.site.register(User)
admin.site.register(Payment)
admin.site.register(Notifications)
