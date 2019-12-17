import datetime
import pytz

from celery import shared_task
from celery.utils.log import get_task_logger

from .helpers.commission_handler import CommissionHandler
from .models import User

logger = get_task_logger(__name__)


@shared_task(name='withdraw')
def auto_withdraw():
    for user in User.objects.all():
        now = datetime.datetime.now().replace(tzinfo=pytz.utc)
        if user.auto_withdraw_is_enabled and user.last_withdraw + datetime.timedelta(days=30) < now:
            logger.info(f'{user} - get his money')
            #  user.last_withdraw = now  # some withdraw function
            #  user.balance = 0
            commission_handler = CommissionHandler(user)
            commission_handler.validate_over_currency({'money': user.balance * 0.9})
            user.save()
