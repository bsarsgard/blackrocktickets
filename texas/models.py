"""
    Texas - Ticket Sales System
    Copyright (C) 2010 Ben Sarsgard

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import random
import string
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from paypal import PayPal
from django.db import connection, transaction
from django.conf import settings
from django.contrib.sites.models import Site
from MarketplaceWidgetUtils import getMarketplaceWidgetForm

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    address_1 = models.CharField(max_length=50, blank=True, null=True)
    address_2 = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    nick_name = models.CharField(max_length=50, blank=True, null=True)

    def __unicode__(self):
        return self.user.__unicode__()

class Event(models.Model):
    site = models.ForeignKey(Site)
    header = models.CharField(max_length=255)
    label = models.CharField(max_length=50)
    description = models.TextField()
    admin_email = models.CharField(max_length=255)
    survival_guide = models.CharField(max_length=255, blank=True, null=True)
    waiver = models.CharField(max_length=255, blank=True, null=True)
    receipt_text = models.TextField(blank=True, null=True)
    paypal_user = models.CharField(max_length=255, blank=True, null=True)
    paypal_password = models.CharField(max_length=255, blank=True, null=True)
    paypal_signature = models.CharField(max_length=255, blank=True, null=True)
    paypal_currency = models.CharField(max_length=3, blank=True, null=True)

    admins = models.ManyToManyField(User)

    def get_active_occurrences(self):
        return Occurrence.objects.filter(event=self,
                end_date__gte=datetime.now())

    def __unicode__(self):
        return self.label

class Option(models.Model):
    label = models.CharField(max_length=255)
    description = models.TextField()
    price = models.FloatField(blank=True, null=True)

    def __unicode__(self):
        return self.label

class Coupon(models.Model):
    label = models.CharField(max_length=50)
    key = models.CharField(max_length=15, default=''.join(
            random.Random().sample(string.letters+string.digits, 15)))
    discount = models.FloatField()
    cap = models.PositiveSmallIntegerField(blank=True, null=True)

    def __unicode__(self):
        return "%s - %s" % (self.label, self.key)

class Occurrence(models.Model):
    event = models.ForeignKey(Event)
    label = models.CharField(max_length=50)
    code = models.CharField(max_length=1)
    start_date = models.DateTimeField('Start date')
    end_date = models.DateTimeField('End date')
    cap = models.PositiveSmallIntegerField(blank=True, null=True)
    description = models.TextField()
    options = models.ManyToManyField(Option, blank=True, null=True)
    coupons = models.ManyToManyField(Coupon, blank=True, null=True)
    allow_donations = models.BooleanField(default=False)

    def get_tickets_purchased(self):
        tickets_purchased = 0
        for tier in self.tier_set.all():
            tickets_purchased += tier.get_tickets_purchased()
        return tickets_purchased

    def get_tickets_available(self):
        if self.cap is None:
            return None
        else:
            return self.cap - self.get_tickets_purchased()

    def get_past_tiers(self):
        return Tier.objects.filter(occurrence=self,
                end_date__lte=datetime.now())

    def get_future_tiers(self):
        return Tier.objects.filter(occurrence=self,
                start_date__gte=datetime.now(), password="")

    def get_active_tiers(self):
        return Tier.objects.filter(occurrence=self,
                start_date__lte=datetime.now(), end_date__gte=datetime.now())

    """
    def get_reservation_tiers(self, user):
        reservations = Reservation.objects.filter(occurrence=self,
                email=user.email)
        purchased_tickets = Ticket.objects.filter(purchase__user=user,
                purchase__occurrence=occurrence)
        if reservations.count() > purchase_tickets.count():
            return Tier.objects.filter(occurrence=self,
                    start_date__lte=datetime.now(),
                    end_date__gte=datetime.now(), reservation_required=True)
    """

    def __unicode__(self):
        return "%s, %s" % (self.event.__unicode__(), self.label)

class Tier(models.Model):
    occurrence = models.ForeignKey(Occurrence)
    label = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=1)
    start_date = models.DateTimeField('Start date')
    end_date = models.DateTimeField('End date')
    price = models.FloatField()
    cap = models.PositiveSmallIntegerField(blank=True, null=True)
    password = models.CharField(max_length=15, blank=True, null=True)
    use_queue = models.BooleanField(default=False)
    max_purchase = models.PositiveSmallIntegerField(default=6)
    reservation_required = models.BooleanField(default=False)

    def get_tickets_purchased(self):
        tickets_paid = self.ticket_set.filter(
                purchase__status='P').count()
        tickets_tentative = self.ticket_set.filter(
                purchase__status='T',
                purchase__expiration_date__gt=datetime.now()).count()
        tickets_requested = 0
        purchase_requests = PurchaseRequest.objects.filter(tier=self,
                purchase__isnull=True,
                expiration_date__gt=datetime.now())
        for request in purchase_requests:
            tickets_requested += request.tickets_requested
        return tickets_paid + tickets_tentative + tickets_requested

    def get_ticket_count(self):
        tickets_paid = self.ticket_set.filter(
                purchase__status='P').count()
        return tickets_paid

    def get_tickets_available(self):
        tickets_available = self.raw_tickets_available()

        if tickets_available < 0:
            tickets_available = 0
        elif tickets_available > self.max_purchase:
            tickets_available = self.max_purchase
        return tickets_available

    def raw_tickets_available(self):
        tickets_available = 0
        if self.cap is None:
            tickets_available = self.max_purchase
        else:
            tickets_available = self.cap - self.get_tickets_purchased()
        if self.occurrence.cap is not None:
            occurrence_available = self.occurrence.get_tickets_available()
            if occurrence_available < tickets_available:
                tickets_available = occurrence_available

        return tickets_available

    def get_ticket_range(self):
        return range(self.get_tickets_available() + 1)

    def get_ticket_list(self):
        return self.ticket_set.all().order_by('assigned_name')

    def get_ticket_set_for_list(self):
        return self.ticket_set.filter(purchase__status='P').order_by(
                'assigned_name')

    def __unicode__(self):
        return "%s, %s" % (self.occurrence.__unicode__(), self.label)

class PaymentMethod(models.Model):
    label = models.CharField(max_length=50);
    time_limit_display = models.TimeField();
    time_limit = models.TimeField();

class Purchase(models.Model):
    STATUS_CHOICES = (
        ('T', 'Tentative'),
        ('H', 'Held'),
        ('P', 'Paid'),
        ('D', 'Deleted'),
    )

    user = models.ForeignKey(User)
    occurrence = models.ForeignKey(Occurrence)
    coupon = models.ForeignKey(Coupon, blank=True, null=True)
    purchase_date = models.DateTimeField('Purchase date',
            default=datetime.now())
    expiration_date = models.DateTimeField('Expiration date',
            blank=True, null=True)
    tickets_requested = models.PositiveSmallIntegerField(default=0)
    payment_method = models.ForeignKey(PaymentMethod, blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='T')
    amount_due = models.FloatField(default=0)
    token = models.CharField(max_length=50, blank=True, null=True)
    options = models.ManyToManyField(Option, blank=True, null=True)

    def get_price(self):
        #price = 0.0
        #for ticket in self.ticket_set.all():
        #    price += ticket.tier.price
        #return price
        return self.amount_due

    def get_paypal_url(self):
        site = Site.objects.get(id=settings.SITE_ID)
        paypal = PayPal(user=self.occurrence.event.paypal_user,
                password=self.occurrence.event.paypal_password,
                signature=self.occurrence.event.paypal_signature,
                return_url='http://%s/buy/paypal_return/' % site.domain,
                cancel_url='http://%s/buy/paypal_cancel/' % site.domain)
        price = self.get_price()
        currency = self.occurrence.event.paypal_currency
        if not currency:
            currency = 'USD'
        token = paypal.SetExpressCheckout(price, currency)
        self.token = token
        self.save()
        paypal_url = paypal.PAYPAL_URL + token
        return paypal_url

    def get_amazon_form(self):
        return getMarketplaceWidgetForm("USD %s" % self.amount_due,
                "Playa del Fuego Ticket Payment", str(self.id),
                "1", "http://tickets.playadelfuego.org/buy/amazon_process/",
                "http://tickets.playadelfuego.org/buy/amazon_cancel/", "1",
                "http://tickets.playadelfuego.org/buy/amazon_instantpaymentnotification/",
                "tickets@playadelfuego.org")

    def __unicode__(self):
        return "%s: %s" % (self.occurrence, self.tickets_requested)

class PurchaseRequest(models.Model):
    tier = models.ForeignKey(Tier)
    ip_address = models.CharField(max_length=15)
    tickets_requested = models.PositiveSmallIntegerField()
    request_date = models.DateTimeField('Request date', default=datetime.now())
    expiration_date = models.DateTimeField('Expiration date', blank=True,
            null=True)
    purchase = models.ForeignKey(Purchase, blank=True, null=True)
    options = models.ManyToManyField(Option)
    coupon = models.ForeignKey(Coupon, blank=True, null=True)
    donation_amount = models.FloatField(blank=True, null=True)
    queue_code = models.CharField(max_length=10, blank=True, null=True)

    def __unicode__(self):
        return "%s, %i" % (self.ip_address, self.tickets_requested)

class Payment(models.Model):
    purchase = models.ForeignKey(Purchase)
    payment_date = models.DateTimeField('Payment date', default=datetime.now())
    amount = models.FloatField()
    reference = models.CharField(max_length=50)
    purchaser_name = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return "%s, %s: %f" % (self.purchase.__unicode__(), self.payment_date, self.amount)

class Reservation(models.Model):
    email = models.CharField(max_length=255)
    occurrence = models.ForeignKey(Occurrence)
    tickets_granted = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return "%s: %s - %i" % (self.occurrence.__unicode__(), self.email,
                self.tickets_granted)

class Comp(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(max_length=75, blank=True, null=True)
    address_1 = models.CharField(max_length=50, blank=True, null=True)
    address_2 = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip = models.CharField(max_length=10, blank=True, null=True)

class Ticket(models.Model):
    tier = models.ForeignKey(Tier)
    comp = models.ForeignKey(Comp, blank=True, null=True)
    purchase = models.ForeignKey(Purchase, blank=True, null=True)
    assigned_user = models.ForeignKey(User, blank=True, null=True)
    assigned_name = models.CharField(max_length=255, blank=True, null=True)
    number = models.PositiveSmallIntegerField(blank=True, null=True)
    code = models.CharField(max_length=4, blank=True, null=True)

    def set_code(self):
        self.code = ''.join([random.choice(string.digits) for i in range(4)])

    def set_number(self):
        number = 1
        cursor = connection.cursor()
        cursor.execute("""
SELECT MAX(number)
FROM texas_ticket
INNER JOIN texas_tier ON texas_tier.id = texas_ticket.tier_id
WHERE texas_tier.occurrence_id = %i
        """ % self.tier.occurrence.id);
        row = cursor.fetchone()
        if row[0] is not None:
            number = row[0] + 1
        self.number = number
        self.save()

    def __unicode__(self):
        return "%s - %s" % (self.tier.__unicode__(), self.number)

