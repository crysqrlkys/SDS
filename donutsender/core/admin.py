from django.contrib import admin

from donutsender.core.models import User, Notifications, Payment, PaymentPage, CashRegister, Withdrawal

admin.site.register(User)
admin.site.register(Payment)
admin.site.register(Notifications)
admin.site.register(PaymentPage)
admin.site.register(Withdrawal)
admin.site.register(CashRegister)
