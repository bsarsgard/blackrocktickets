from django.core.management.base import NoArgsCommand, BaseCommand
from django.core.mail import send_mail, EmailMessage
from optparse import make_option
from texas.models import *
from datetime import datetime
import random
import string
import time

class Command(BaseCommand):
    args = "<occurrence_id>"
    help = "Send email blast to purchasers"

    def handle(self, *args, **options):
        occurrence_id = args[0]
        purchases = Purchase.objects.filter(occurrence__id=occurrence_id,
            status='P').order_by('user__email');
	#purchases = purchases.filter(user__email='bsarsgard@slightlymad.net')

        last_email = ''
        for purchase in purchases:
            if purchase.user.email == last_email:
                print 'skip'
            else:
                print purchase.user.email
                event = purchase.occurrence.event
                site = Site.objects.get(id=settings.SITE_ID)
                subject = "New Ticketing Hours for %s - Please Read" % event.label
                from_address = "tickets@playadelfuego.org"
                to_address = [purchase.user.email]
		body = """Just 1 day away from the Fall Burn and I wanted to get some important information out to you.  There will be new Ticketing Hours for this burn

Thursday 5pm - Friday 3am (CLOSED 3am - 9am)
Friday 9am - Saturday 1:30am (CLOSED 1:30am - 9am)
Saturday 9am - Saturday 8pm (CLOSED After 8pm till the end of the event)
Sunday - CLOSED
Monday - CLOSED

If you show up during closed hours, you will be asked to leave the site until 9am the following morning.  There will be no hanging out in the parking lot during closed hours.

As the ticket purchaser it is your responsibility to forward this information on to those you purchased tickets for.  Please pass it along to everyone you know who has a ticket.

Thank You!"""
                if False and event.survival_guide:
                    body += """\n\nYour survival guide for the event is attached, please review it at your convenince."""
                email = EmailMessage(subject, body, from_address, to_address)
                if False and event.survival_guide:
                    try:
                        email.attach_file("/srv/django/tickets/static/%s" % (event.survival_guide))
                    except:
                        pass
                email.send()
                time.sleep(1)
                
            last_email = purchase.user.email
