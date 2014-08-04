from django.core.management.base import NoArgsCommand, BaseCommand
from optparse import make_option
from texas.models import *
from datetime import datetime
import random
import string

class Command(BaseCommand):
    args = "<label discount quantity cap>"
    help = "Create coupons"

    def handle(self, *args, **options):
        label = args[0]
        discount = float(args[1])
        quantity = int(args[2])
        if args[3]:
            cap = int(args[3])
        else:
            cap = None

        for ii in range(0, quantity):
            key = ''
            while key == '' or key.find('I') != -1 or key.find('i') != -1 or key.find('o') != -1 or key.find('O') != -1 or key.find('l') != -1 or key.find('L') != -1:
                key = default=''.join(
                        random.Random().sample(string.letters+string.digits,
                        6))
            coupon_label = "%s %i" % (label, ii)
            print key
            coupon = Coupon(label=coupon_label, key=key, discount=discount,
                    cap=cap)
            coupon.save()
