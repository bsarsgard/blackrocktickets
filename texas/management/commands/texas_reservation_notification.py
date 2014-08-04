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
        reservations = Reservation.objects.filter(
                occurrence__id=occurrence_id).order_by('email');
	#reservations = reservations.filter(email='bsarsgard@slightlymad.net')

        last_email = ''
        for reservation in reservations:
                print reservation.email
                event = reservation.occurrence.event
                site = Site.objects.get(id=settings.SITE_ID)
                subject = "%s Reserve Ticket Notification" % event.label
                from_address = "tickets@playadelfuego.org"
                to_address = [reservation.email]
                body = """Due to your essential nature for the %s event, you have been approved for the reserve ticket tier.  Your reservation is tied to this email address, so you must log in with an account matching it.  If you'd prefer to use a different email address, or have been granted multiple tickets and would like to transfer some or all of them to another essential member of your team, please reply to this email.

Email address: %s
Reserve ticket quantity: %i

To purchase, please login in with the above email address, then click "Buy Tickets"
http://%s/login/

Please make your purchases immediately, as reserve ticket sales will end at midnight, the night before the next round of sales.

If you receive multiple copies of this email, it is because you have been granted reserve tickets for multiple volunteer positions.  The total number of reserve tickets granted is the sum of all quantities in notices received.""" % (
                        reservation.occurrence, reservation.email,
                        reservation.tickets_granted, site.domain)
                email = EmailMessage(subject, body, from_address, to_address)
                email.send()
                time.sleep(1)
                last_email = reservation.email
