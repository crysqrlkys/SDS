from django.contrib import admin

from donutsender.core.models import *

admin.site.register(User)
admin.site.register(Payment)
admin.site.register(Settings)
admin.site.register(PaymentPage)
admin.site.register(Withdrawal)
admin.site.register(CashRegister)
admin.site.register(FirebaseUser)
