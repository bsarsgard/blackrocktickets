from django.core.management.base import NoArgsCommand, BaseCommand
from django.core.mail import send_mail, EmailMessage
from optparse import make_option
from texas.models import *
from datetime import datetime
import random
import string
import time

class Command(BaseCommand):
    args = "<tier_id> <count>"
    help = "Send lottery notification to purchasers"

    def handle(self, *args, **options):
        tier_id = args[0]
        count = int(args[1])
        chances = Chance.objects.filter(
                queue_code__isnull=True).order_by('?')
	#chances = chances.filter(user__email='bsarsgard@slightlymad.net')
        chances = chances[:count]

        chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
        for chance in chances:
            print chance.user.email
            code = ''.join(random.choice(chars) for _ in range(10))
            chance.queue_code = code
            chance.save()
            event = chance.tier.occurrence.event
            site = Site.objects.get(id=settings.SITE_ID)
            subject = "Your %s lottery entry" % event.label
            from_address = "tickets@playadelfuego.org"
            to_address = [chance.user.email]
            body = """Congratulations! Your lottery entry has been selected to proceed!

Your entry will expire 72 hours from the date on this email, so please proceed as soon as you can. Once you have selected your number of tickets, your lottery code will be considered used, and you will not be able to complete a second purchase, so be sure you have everything in order before proceeding.

You will need to be logged in with the account you used to enter the lottery, so please do so before clicking the link. We also suggest logging into PayPal ahead of time to be sure your account is working.

http://%s/buy/?show=show&code=%s

Thank You!""" % (
                site.domain,
                chance.queue_code,
            )
            email = EmailMessage(subject, body, from_address, to_address)
            email.send()
            time.sleep(1)
        print 'done'
