from django.core.management.base import NoArgsCommand, BaseCommand
from optparse import make_option
from txqueue.models import QueuedTier
from datetime import datetime
import random
import string

class Command(BaseCommand):
    args = "<name url start_date start_time max_tickets cap>"
    help = "Create a new queued tier"

    def handle(self, *args, **options):
        name = args[0]
        url = args[1]
        starts = datetime.strptime(args[2]+' '+args[3], "%Y-%m-%d %H:%M:%S")
        max_tickets = int(args[4])
        cap = int(args[5])

        tier = QueuedTier(name=name, url=url, starts=starts,
                max_tickets=max_tickets, cap=cap)
        tier.save()
