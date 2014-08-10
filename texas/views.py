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

from django.http import HttpResponse
from django.views.generic.simple import direct_to_template, redirect_to
from tickets.texas.models import *
from tickets.texas.forms import *
from datetime import datetime
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from paypal import PayPal
from django.core.mail import send_mail, EmailMessage
from random import Random
from django.conf import settings
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from utils import *
from urllib import urlopen
import queries

def index(request):
    events = Event.objects.filter(occurrence__end_date__gte=datetime.now())
    return direct_to_template(request, 'texas/index.html', {'events': events})

def view_event(request, event_id):
    events = Event.objects.filter(pk=event_id)
    return direct_to_template(request, 'texas/index.html', {'events': events})

def test(request):
    return direct_to_template(request, 'texas/test.html')

def about(request):
    return direct_to_template(request, 'texas/about.html')

def comps(request):
    return direct_to_template(request, 'texas/comps.html')

def contact(request):
    events = Event.objects.filter(occurrence__end_date__gte=datetime.now())
    return direct_to_template(request, 'texas/contact.html', {'events': events})

def terms(request):
    return direct_to_template(request, 'texas/terms.html')

def event_admin(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if not request.user in event.admins.all():
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or lacking admin privileges"})
    return direct_to_template(request, 'texas/event_admin.html',
            {'event': event})

def occurrence_admin_ticket_list(request, occurrence_id):
    occurrence = get_object_or_404(Occurrence, pk=occurrence_id)
    if not request.user in occurrence.event.admins.all():
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or lacking admin privileges"})
    return direct_to_template(request,
            'texas/occurrence_admin_ticket_list.html',
            {'occurrence': occurrence})

def occurrence_admin_ticket_export(request, occurrence_id):
    occurrence = get_object_or_404(Occurrence, pk=occurrence_id)
    if not request.user in occurrence.event.admins.all():
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or lacking admin privileges"})
    response = direct_to_template(request,
            'texas/occurrence_admin_ticket_export.xml',
            {'occurrence': occurrence})
    filename = "brt_ticket_export.xml"
    response['Content-Disposition'] = 'attachment; filename='+filename
    response['Content-Type'] = 'text/xml'
    return response

def occurrence_admin_ticket_stats(request, occurrence_id):
    occurrence = get_object_or_404(Occurrence, pk=occurrence_id)
    if not request.user in occurrence.event.admins.all():
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or lacking admin privileges"})

    sales_from = None
    sales_to = None
    for tier in occurrence.tier_set.all():
        if not sales_from or sales_from < tier.start_date:
            sales_from = tier.start_date
        if not sales_to or sales_to > tier.end_date:
            sales_to = tier.end_date

    cursor = connection.cursor()
    cursor.execute(queries.TICKETS_SOLD_BY_DAYS, [occurrence.id])
    tickets_sold_by_days = cursor.fetchall()
    #tickets_sold_by_days = explode_history(sales_from, sales_to,
    #        tickets_sold_by_days)
    cursor = connection.cursor()
    cursor.execute(queries.TICKETS_SOLD_BY_MONTH, [occurrence.id])
    tickets_sold_by_month = cursor.fetchall()
    cursor = connection.cursor()
    cursor.execute(queries.TICKETS_SOLD_BY_TIER, [occurrence.id])
    tickets_sold_by_tier = cursor.fetchall()
    cursor = connection.cursor()
    cursor.execute(queries.USERS_BY_TICKET_COUNT, [occurrence.id])
    users_by_ticket_count = cursor.fetchall()
    cursor = connection.cursor()
    cursor.execute(queries.AVG_TICKETS_BY_TIER, [occurrence.id])
    avg_tickets_by_tier = cursor.fetchall()

    return direct_to_template(request,
            'texas/occurrence_admin_ticket_stats.html',
            {'occurrence': occurrence, 'tickets_sold_by_days':
            tickets_sold_by_days, 'tickets_sold_by_month':
            tickets_sold_by_month, 'tickets_sold_by_tier':
            tickets_sold_by_tier, 'users_by_ticket_count':
            users_by_ticket_count, 'avg_tickets_by_tier':
            avg_tickets_by_tier})

def occurrence_admin_option_list(request, occurrence_id):
    occurrence = get_object_or_404(Occurrence, pk=occurrence_id)
    if not request.user in occurrence.event.admins.all():
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or lacking admin privileges"})
    return direct_to_template(request,
            'texas/occurrence_admin_option_list.html',
            {'occurrence': occurrence})

def occurrence_admin_sale(request, occurrence_id):
    occurrence = get_object_or_404(Occurrence, pk=occurrence_id)
    if not request.user in occurrence.event.admins.all():
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or lacking admin privileges"})

    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            tickets = form.cleaned_data['tickets']
            email = form.cleaned_data['email']

            try:
                user = User.objects.get(email=email)
            except:
                user = None

            if not user:
                user = User.objects.create_user(username=email, email=email,
                        password='')
                user.first_name = ''.join(Random().sample(
                    string.letters+string.digits, 5))
                user.is_active = False
                user.save()

            tier = Tier.objects.get(pk=request.POST['tier_id'])
            purchase = Purchase(user=user, occurrence=occurrence,
                    purchase_date=datetime.now(), tickets_requested=tickets,
                    status='P', amount_due=0)
            purchase.save()
            for ii in range(0, int(tickets)):
                ticket = Ticket(tier=tier, purchase=purchase)
                ticket.assigned_name = name
                ticket.set_code()
                ticket.set_number()
                ticket.save()

            if user.is_active:
                # send purchase email
                do_send_purchase_confirmation(purchase)
            else:
                # send notification email
                do_send_sale_notification(purchase)

            form = SaleForm()
            return direct_to_template(request,
                    'texas/occurrence_admin_sale.html', {'form': form,
                    'occurrence': occurrence, 'message': "Purchase Added"})
        else:
            form = SaleForm()
            return direct_to_template(request,
                    'texas/occurrence_admin_sale.html', {'form': form,
                    'occurrence': occurrence, 'message': "Error"})
    else:
        form = SaleForm()
        return direct_to_template(request,
                'texas/occurrence_admin_sale.html', {'form': form,
                'occurrence': occurrence})

def amazon_process(request):
    try:
        tid = request.GET.get('transactionId')
        pid = request.GET.get('referenceId')
        amt = request.GET.get('transactionAmount')
        name = request.GET.get('buyerName')

        purchase = Purchase.objects.get(pk=pid)
        if amt != "USD %s" % purchase.amount_due:
            return direct_to_template(request, 'texas/error.html',
                {'message': "Payment amount does not match!"})
        payment = Payment(purchase=purchase, amount=purchase.get_price(),
                reference=tid)
        payment.purchaser_name = name
        payment.save()
        if payment.amount >= purchase.amount_due:
            purchase.status = 'P'
            purchase.save()
            for ticket in purchase.ticket_set.all():
                ticket.assigned_name = payment.purchaser_name
                ticket.set_code()
                ticket.set_number()
            do_send_purchase_confirmation(purchase)
        return redirect_to(request, "/buy/purchases/receipt/%i/" % purchase.id)
        return direct_to_template(request, 'texas/error.html',
            {'message': "Payment error!"})
    except:
        return direct_to_template(request, 'texas/error.html',
            {'message': "Amazon payment error!  Please contact tickets@blackrocktickets.com and make a payment via PayPal.  We will refund your Amazon payment promptly if notified."})

def amazon_cancel(request):
    return direct_to_template(request, 'texas/paypal_cancel.html')

def amazon_ipn(request):
    return direct_to_template(request, 'texas/paypal_cancel.html')

def donate_thanks(request):
    return direct_to_template(request, 'texas/donate_thanks.html')

def donate_ohwell(request):
    return direct_to_template(request, 'texas/donate_ohwell.html')

def donate_instantpaymentnotification(request):
    return direct_to_template(request,
            'texas/donate_instantpaymentnotification.html')

def buy(request):
    occurrences = Occurrence.objects.all().exclude(pk=11)
    if request.method == 'POST':
        # form submission
        return do_buy(request, occurrences)
    else:
        show = request.GET.get('show', '')
        for occurrence in occurrences:
            for tier in occurrence.tier_set.all():
                foo = tier.get_ticket_range()
        code = None
        need_code = False
        for occurrence in occurrences:
            for tier in occurrence.get_active_tiers():
                if tier.use_queue:
                    need_code = True
                    break
            if need_code:
                break
        if need_code:
            code = get_code(request)
            if code:
                show = "show"
            if code and not check_queue_code(code):
                return direct_to_template(request, 'texas/error.html',
                    {'message': "Invalid queue code!"})
        response = direct_to_template(request, 'texas/buy.html', {'occurrences':
            occurrences, 'code': code, 'queue_url': settings.QUEUE_URL,
            'show': show})
        if code:
            max_age = 24*60*60
            expires = datetime.strftime(
                    datetime.utcnow() + timedelta(seconds=max_age),
                    "%a, %d-%b-%Y %H:%M:%S GMT")
            response.set_cookie('code', code, max_age, expires)
        return response

def get_code(request):
    code = request.GET.get('code', None)
    if not code:
        # check for code in session
        if 'code' in request.COOKIES:
            code = request.COOKIES['code']
            if not check_queue_code(code):
                # if it's bad, ignore it
                code = None
    return code

def buy_occurrence(request, occurrence_id):
    occurrences = Occurrence.objects.filter(pk=occurrence_id)
    if request.method == 'POST':
        # form submission
        return do_buy(request, occurrences)
    else:
        # loading form
        show = request.GET.get('show', '')
        code = None
        need_code = False
        for occurrence in occurrences:
            for tier in occurrence.get_active_tiers():
                if tier.use_queue:
                    need_code = True
                    break
            if need_code:
                break
        if need_code:
            code = get_code(request)
            if code:
                show = "show"
        if code and not check_queue_code(code):
            return direct_to_template(request, 'texas/error.html',
                {'message': "Invalid queue code!"})
        response = direct_to_template(request, 'texas/buy.html', {'occurrences':
            occurrences, 'code': code, 'queue_url': settings.QUEUE_URL,
            'show': show})
        if code:
            max_age = 24*60*60
            expires = datetime.strftime(
                    datetime.utcnow() + timedelta(seconds=max_age),
                    "%a, %d-%b-%Y %H:%M:%S GMT")
            response.set_cookie('code', code, max_age, expires)
        return response

def check_queue_code(code):
    f = urlopen("%s/check/%s" % (settings.QUEUE_URL, code))
    response = f.read().rstrip("\n")
    if response == '1':
        return True
    else:
        return False

def use_queue_code(code, tickets):
    f = urlopen("%s/use/%s?tix=%i" % (settings.QUEUE_URL, code, tickets))
    response = f.read().rstrip("\n")
    if response == '1':
        return True
    else:
        return False

def pay_queue_code(code):
    f = urlopen("%s/pay/%s" % (settings.QUEUE_URL, code))
    response = f.read().rstrip("\n")
    if response == '1':
        return True
    else:
        return False

def do_buy(request, occurrences):
    code = request.POST.get('code', None)
    total_tickets = 0
    ip_address = request.META['REMOTE_ADDR']

    # coupon
    coupon = None
    cou = request.POST.get("coupon", None)
    if cou:
        try:
            coupon = Coupon.objects.get(key=cou)
            if coupon.cap <= coupon.purchaserequest_set.filter(
                    purchase__isnull=True).count() +\
                    coupon.purchase_set.count():
                return direct_to_template(request, 'texas/buy.html',
                        {'occurrences': occurrences,
                        'error': 'Coupon already used!', 'code': code})
        except:
            return direct_to_template(request, 'texas/buy.html',
                    {'occurrences': occurrences,
                    'error': 'Invalid coupon code!', 'code': code})

    for occurrence in occurrences:
        for tier in occurrence.tier_set.all():
            tickets_requested = int(
                    request.POST.get("tickets_%i" % tier.id, 0))
            if tickets_requested > 0:
                if tier.reservation_required:
                    if not request.user.is_authenticated():
                        form = LoginForm()
                        message = "Please log in before purchasing."
                        return direct_to_template(request,
                                'registration/login.html', {'form': form,
                                'message': message})
                    tickets_purchased = Ticket.objects.filter(
                            purchase__user=request.user,
                            tier__occurrence=occurrence,
                            purchase__status='P')
                    tickets_pending = Ticket.objects.filter(
                            purchase__user=request.user,
                            tier__occurrence=occurrence,
                            purchase__status='T',
                            purchase__expiration_date__gt=datetime.now())
                    reservations = Reservation.objects.filter(
                            email=request.user.email, occurrence=occurrence)
                    reservation_count = 0
                    for reservation in reservations:
                        reservation_count += reservation.tickets_granted
                    all_tickets = tickets_purchased.count() + \
                            tickets_pending.count() + tickets_requested
                    if reservation_count < all_tickets:
                        return direct_to_template(request, 'texas/buy.html',
                                {'occurrences': occurrences,
                                'error': 'Reservation required!', 'code': code})
                if tier.password != "":
                    if request.POST.get(
                            "password_%i" % tier.id, "") != tier.password:
                        return direct_to_template(request, 'texas/buy.html',
                                {'occurrences': occurrences,
                                'error': 'Incorrect password!', 'code': code})
                if tier.use_queue and code:
                    if not use_queue_code(code, tickets_requested):
                        return direct_to_template(request, 'texas/error.html',
                                {'message': "Invalid queue code!"})
                total_tickets += tickets_requested
                request_date = datetime.now()
                expires = timedelta(minutes=15)
                expiration_date = request_date + expires
                purchase_request = PurchaseRequest(tier=tier,
                        ip_address=ip_address,
                        tickets_requested=tickets_requested,
                        request_date=request_date,
                        expiration_date=expiration_date, coupon=coupon,
                        queue_code=code)
                # add donation if present
                #donation_amount = request.POST.get("donation_%i" % tier.id, "")
                donation_amount = ""
                if donation_amount != "":
                    try:
                        purchase_request.donation_amount =\
                                float(donation_amount)
                    except:
                        pass
                purchase_request.save()
                # add options
                for option in occurrence.options.all():
                    opt = request.POST.get("option_%s" % option.id, None)
                    if opt:
                        purchase_request.options.add(option)

    if total_tickets == 0:
        return direct_to_template(request, 'texas/buy.html', {'occurrences':
                occurrences, 'error': 'You have not selected anything!',
                'code': code})
    else:
        # purchases were requested
        if request.user.is_authenticated():
            ip_address = request.META['REMOTE_ADDR']
            do_process_requests(ip_address, request.user)
            return redirect_to(request, '/buy/purchases/')
        else:
            return redirect_to(request, '/buy/requests/')

def do_process_requests(ip_address, user):
    purchase_requests = PurchaseRequest.objects.filter(
            ip_address=ip_address
    ).exclude(
            purchase__isnull=False
    ).exclude(
            expiration_date__lte=datetime.now()
    )

    if purchase_requests.count() > 0:
        purchase_date = datetime.now()
        expires = timedelta(minutes=30)
        expiration_date = purchase_date + expires
        for purchase_request in purchase_requests:
            # turn into real purchases
            purchase = Purchase(user=user,
                    occurrence=purchase_request.tier.occurrence,
                    purchase_date=purchase_date,
                    expiration_date=expiration_date,
                    tickets_requested=purchase_request.tickets_requested,
                    coupon=purchase_request.coupon)
            # check ticket available count here
            # add current request to available count, since it's already
            # subtracted from the count
            available = purchase_request.tier.raw_tickets_available() +\
                    purchase_request.tickets_requested
            if available < purchase_request.tickets_requested:
                if available < 1:
                    purchase.tickets_requested = 0
                else:
                    purchase.tickets_requested = available
            if purchase.tickets_requested > 0:
                purchase.save()
                purchase.options = purchase_request.options.all()
                for ii in range(purchase.tickets_requested):
                    ticket = Ticket(tier=purchase_request.tier,
                            purchase=purchase)
                    ticket.save()
                    purchase.amount_due += ticket.tier.price
                if purchase.coupon:
                    purchase.amount_due -= purchase.coupon.discount
                for option in purchase.options.all():
                    if option.price:
                        purchase.amount_due += option.price
                #if purchase_request.donation_amount:
                #    purchase.amount_due += purchase_request.donation_amount
                if purchase.amount_due <= 0:
                    purchase.amount_due = 0
                    purchase.status = 'P'
                purchase_request.purchase = purchase
                purchase_request.save()
                purchase.save()

def requests(request):
    ip_address = request.META['REMOTE_ADDR']
    purchase_requests = PurchaseRequest.objects.filter(
            ip_address=ip_address
    ).exclude(
            purchase__isnull=False
    ).exclude(
            expiration_date__lte=datetime.now()
    )
    return direct_to_template(request, 'texas/purchase_requests.html',
            {'purchase_requests': purchase_requests})

def tickets(request):
    if not request.user.is_authenticated():
        form = LoginForm()
        message = "Please log in to continue."
        return direct_to_template(request,
                'registration/login.html', {'form': form,
                'message': message})
    if request.method == 'POST':
        if request.POST.get('action', '') == 'transfer':
            email = request.POST.get('email', '')
            ticket_id = request.POST.get('ticket_id', '')
            ticket = Ticket.objects.get(pk=ticket_id)
            if ticket.purchase.user != request.user:
                return direct_to_template(request, 'texas/error.html',
                        {'message': "Access denied"})
            else:
                try:
                    assigned_user = User.objects.get(email__iexact=email)
                except:
                    assigned_user = None

                if not assigned_user:
                    assigned_user = User.objects.create_user(username=email,
                            email=email, password='')
                    assigned_user.first_name = ''.join(Random().sample(
                            string.letters+string.digits, 5))
                    assigned_user.is_active = False
                    assigned_user.save()

                ticket.assigned_user = assigned_user
                #ticket.set_code()
                ticket.save()
                do_send_transfer_notification(ticket)
                return redirect_to(request, '/tickets/')

    paid_purchases = Purchase.objects.filter(
            user=request.user, status='P'
    ).exclude(
            occurrence__end_date__lte=datetime.now()
    )
    assigned_tickets = Ticket.objects.filter(
            assigned_user=request.user, purchase__status='P'
    ).exclude(
            purchase__occurrence__end_date__lte=datetime.now()
    )
    return direct_to_template(request, 'texas/tickets.html',
            {'paid_purchases': paid_purchases,
                    'assigned_tickets': assigned_tickets})

def purchases(request):
    if not request.user.is_authenticated():
        form = LoginForm()
        message = "Please log in to continue."
        return direct_to_template(request,
                'registration/login.html', {'form': form,
                'message': message})
    tentative_purchases = Purchase.objects.filter(
            user=request.user, status='T'
    ).exclude(
            expiration_date__lte=datetime.now()
    ).exclude(
            occurrence__end_date__lte=datetime.now()
    ).order_by('-purchase_date')
    expired_purchases = Purchase.objects.filter(
            user=request.user, status='T'
    ).exclude(
            expiration_date__gt=datetime.now()
    ).exclude(
            occurrence__end_date__lte=datetime.now()
    ).order_by('-purchase_date')
    paid_purchases = Purchase.objects.filter(
            user=request.user, status='P'
    ).exclude(
            occurrence__end_date__lte=datetime.now()
    ).order_by('-purchase_date')
    held_purchases = Purchase.objects.filter(
            user=request.user, status='H'
    ).exclude(
            occurrence__end_date__lte=datetime.now()
    ).order_by('-purchase_date')
    old_purchases = Purchase.objects.filter(
            user=request.user, status='P',
            occurrence__end_date__lte=datetime.now()
    ).order_by('-purchase_date')
    return direct_to_template(request, 'texas/purchases.html',
            {'tentative_purchases': tentative_purchases, 'expired_purchases':
            expired_purchases, 'paid_purchases': paid_purchases,
            'held_purchases': held_purchases, 'old_purchases': old_purchases})

def purchase_pay(request, purchase_id):
    purchase = Purchase.objects.get(pk=purchase_id)
    if purchase.user != request.user and not request.user.is_superuser:
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or order does not match logged in user"})
    elif purchase.get_price() == 0.0:
        return direct_to_template(request, 'texas/error.html',
            {'message': 'No payment due on this order'})
    else:
        paypal_url = purchase.get_paypal_url()
        return redirect_to(request, paypal_url)

def purchase_receipt(request, purchase_id):
    purchase = Purchase.objects.get(pk=purchase_id)
    if purchase.user != request.user and not request.user.is_superuser:
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or order does not match logged in user"})
    else:
        return direct_to_template(request, 'texas/purchase_receipt.html',
                {'purchase': purchase})

def purchase_print(request, purchase_id):
    purchase = Purchase.objects.get(pk=purchase_id)
    if purchase.user != request.user and not request.user.is_superuser:
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or order does not match logged in user"})
    else:
        return direct_to_template(request, 'texas/purchase_print.html',
                {'purchase': purchase})

def ticket_print(request, ticket_id):
    ticket = Ticket.objects.get(pk=ticket_id)
    if ticket.assigned_user is None and\
		 ticket.purchase.user != request.user and\
		 not request.user.is_superuser:
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or order does not match logged in user"})
    elif ticket.assigned_user is not None and\
		 ticket.assigned_user != request.user:
        return direct_to_template(request, 'texas/error.html',
            {'message': "This ticket is assigned to another user"})
    else:
        return direct_to_template(request, 'texas/ticket_print.html',
                {'ticket': ticket})

def paypal_return(request):
    token = request.GET.get('token')
    purchase = Purchase.objects.get(token=token)
    if purchase.user != request.user and not request.user.is_superuser:
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or order does not match logged in user"})
    elif purchase.get_price() == 0.0:
        return direct_to_template(request, 'texas/error.html',
            {'message': 'No payment due on this order'})
    site = Site.objects.get(id=settings.SITE_ID)
    event = purchase.occurrence.event
    paypal = PayPal(return_url='http://%s/buy/paypal_return/' % site.domain,
            cancel_url='http://%s/buy/paypal_cancel' % site.domain,
            user=event.paypal_user, password=event.paypal_password,
            signature=event.paypal_signature)
    paypal_details = paypal.GetExpressCheckoutDetails(token,
            return_all=True)
    if 'Success' in paypal_details['ACK']:
        token = paypal_details['TOKEN'][0]
        first_name = paypal_details['FIRSTNAME'][0]
        last_name = paypal_details['LASTNAME'][0]
        return direct_to_template(request, 'texas/paypal_return.html',
                {'purchase': purchase, 'token': token,
                'first_name': first_name, 'last_name': last_name})
    else:
        return direct_to_template(request, 'texas/error.html',
                {'message': 'Paypal has returned an error; payment canceled.'})

def paypal_process(request, purchase_id):
    purchase = Purchase.objects.get(pk=purchase_id)
    if purchase.user != request.user and not request.user.is_superuser:
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or order does not match logged in user"})
    elif purchase.get_price() == 0.0:
        return direct_to_template(request, 'texas/error.html',
            {'message': 'No payment due on this order'})
    token = purchase.token
    site = Site.objects.get(id=settings.SITE_ID)
    event = purchase.occurrence.event
    paypal = PayPal(return_url='http://%s/buy/paypal_return/' % site.domain,
            cancel_url='http://%s/buy/paypal_cancel' % site.domain,
            user=event.paypal_user, password=event.paypal_password,
            signature=event.paypal_signature)
    paypal_details = paypal.GetExpressCheckoutDetails(token,
            return_all=True)
    currency = event.paypal_currency
    if not event.paypal_currency:
        currency = 'USD'
    payment_details  = paypal.DoExpressCheckoutPayment(token=token,
            payer_id=paypal_details['PAYERID'][0], amt=purchase.get_price(),
            currency=currency)
    if 'Success' in payment_details['ACK']:
        first_name = paypal_details['FIRSTNAME'][0]
        last_name = paypal_details['LASTNAME'][0]
        payment = Payment(purchase=purchase, amount=purchase.get_price(),
                reference=token)
        payment.purchaser_name = "%s, %s" % (last_name, first_name)
        payment.save()
        if payment.amount >= purchase.amount_due:
            purchase.status = 'P'
            purchase.save()
            for ticket in purchase.ticket_set.all():
                ticket.assigned_name = payment.purchaser_name
                ticket.set_code()
                ticket.set_number()
            do_send_purchase_confirmation(purchase)
        # update queue
        for purchaserequest in purchase.purchaserequest_set.all():
            if purchaserequest.queue_code:
                pay_queue_code(purchaserequest.queue_code)
        return redirect_to(request, "/buy/purchases/receipt/%i/" % purchase.id)
    else:
        return direct_to_template(request, 'texas/error.html',
                {'message':
                "ack: %s, code: %s, short: %s, long: %s, severity: %s" %
                (payment_details['ACK'], payment_details['L_ERRORCODE0'],
                payment_details['L_SHORTMESSAGE0'],
                payment_details['L_LONGMESSAGE0'],
                payment_details['L_SEVERITYCODE0'])})

def paypal_cancel(request):
    return direct_to_template(request, 'texas/paypal_cancel.html')

def do_send_user_password_reset(user, password):
    site = Site.objects.get(id=settings.SITE_ID)
    subject = "%s Password Reset" % site.name
    from_address = "tickets@%s" % site.domain
    to_address = [user.username]
    body = """Your password has been reset.  If you do not know why you have received this message, please email %s.

To login, please go to the following url:
http://%s/login/

Your new password is: %s

Once you've logged in, you may use the "Change Password" link on the right side of the screen to change it to something you'll remember.

Thanks,
%s""" % (from_address, site.domain, password, site.name)
    send_mail(subject, body, from_address, to_address)

def do_send_transfer_notification(ticket):
    purchase = ticket.purchase
    event = purchase.occurrence.event
    site = Site.objects.get(id=settings.SITE_ID)
    subject = "%s Ticket Transfer" % site.name
    from_address = "tickets@%s" % site.domain
    to_address = [ticket.assigned_user.email]
    body = """A ticket transfer for %s has been processed for this email
address.  To claim it, please create an account (or log in if you already have
one) with THIS EMAIL ADDRESS at http://%s/login/ .

You may then click "My Tickets" on the right side of your screen to print your
ticket.""" % (event, site.domain)
    if event.survival_guide:
        body += """  Your survival guide for the event is attached, please review it at your convenince."""
    email = EmailMessage(subject, body, from_address, to_address)
    if event.survival_guide:
        #email.attach_file("/home/oszo/%s/public/%s" % (site.domain,
        #    event.survival_guide))
        try:
            email.attach_file("/srv/django/tickets/%s" % (event.survival_guide))
        except:
            pass
    email.send()

def do_send_sale_notification(purchase):
    event = purchase.occurrence.event
    site = Site.objects.get(id=settings.SITE_ID)
    subject = "%s Sale Processed" % site.name
    from_address = "tickets@%s" % site.domain
    to_address = [purchase.user.email]
    body = """A ticket sale for %s has been processed for this email address.
To claim it, please create an account with THIS EMAIL ADDRESS at
http://%s/login/ .""" % (event, site.domain)
    if event.survival_guide:
        body += """  Your survival guide for the event is attached, please review it at your convenince."""
    email = EmailMessage(subject, body, from_address, to_address)
    if event.survival_guide:
        try:
            email.attach_file("/home/oszo/%s/public/%s" % (site.domain,
                event.survival_guide))
            #email.attach_file("/srv/django/tickets/%s" % (event.survival_guide))
        except:
            pass
    email.send()

def do_send_purchase_confirmation(purchase):
    event = purchase.occurrence.event
    site = Site.objects.get(id=settings.SITE_ID)
    subject = "%s Purchase Complete" % site.name
    from_address = "tickets@%s" % site.domain
    to_address = [purchase.user.email]
    body = """Thank you for your ticket purchase.  To print your entry pass,
please visit http://%s/buy/purchases/ .""" % site.domain
    if event.survival_guide:
        body += """  Your survival guide for the event is attached, please review it at your convenince."""
    email = EmailMessage(subject, body, from_address, to_address)
    if event.survival_guide:
        #email.attach_file('/home/oszo/blackrocktickets.com/public/media/PH survival guide 2010.pdf')
        try:
            email.attach_file("/home/oszo/%s/public/%s" % (site.domain,
                event.survival_guide))
            #email.attach_file("/srv/django/tickets/%s" % (event.survival_guide))
        except:
            pass
    email.send()

def do_send_new_user_confirmation(user, password):
    # generate a confirm hash
    site = Site.objects.get(id=settings.SITE_ID)
    confirm_url = "http://%s/confirm/%i/%s/" % (site.domain, user.id,
            user.first_name)
    subject = "%s Account Created" % site.name
    from_address = "tickets@%s" % site.domain
    to_address = [user.email]
    body = """You have successfully created an account on the Black Rock
Tickets website!  Please keep this email safe, as it contains valuable account
information.

To confirm your account, please go to the following url:
%s

Email: %s
Password: %s

Thanks,
%s""" % (confirm_url, user.email, password, site.name)
    send_mail(subject, body, from_address, to_address)

def user_login(request):
    if request.method == 'POST':
        if request.POST.get('username', '') == '':
            form = LoginForm()
            message = "Please enter an email address and password."
            return direct_to_template(request, 'registration/login.html',
                    {'form': form, 'message': message})
        if request.POST.get('login_is_new', '0') == '1':
            if request.POST.get('password', '') == '':
                form = LoginForm()
                message = "Please enter an email address and password."
                return direct_to_template(request, 'registration/login.html',
                        {'form': form, 'message': message})
            try:
                try:
                    user = User.objects.get(email=request.POST['username'])
                    user.set_password(request.POST['password'])
                except:
                    user = None

                if user and user.is_active:
                    return direct_to_template(request, 'texas/error.html',
                            {'message': """Could not create user, %s.  This is
                            because the email address is already registered
                            in the system.""" % request.POST['username']})
                elif not user:
                    user = User.objects.create_user(
                            username=request.POST['username'],
                            email=request.POST['username'],
                            password=request.POST['password'])

                user.first_name = ''.join(Random().sample(
                    string.letters+string.digits, 5))
                user.is_active = False
                user.save()

                do_send_new_user_confirmation(user, request.POST['password'])
                ip_address = request.META['REMOTE_ADDR']
                do_process_requests(ip_address, user)
            except Exception, ex:
                return direct_to_template(request, 'texas/error.html',
                        {'message': "Could not create user"})
            return direct_to_template(request, 'registration/new_user.html',
                    {'user': user})
        elif request.POST.get('login_is_new', '0') == '2':
            try:
                password = ''.join(Random().sample(
                    string.letters+string.digits, 5))
                user = User.objects.get(username=request.POST['username'])
                user.set_password(password)
                user.save()
                do_send_user_password_reset(user, password)
                form = LoginForm()
                message = "Your password has been reset and emailed to you."
                return direct_to_template(request, 'registration/login.html',
                    {'form': form, 'message': message})
            except Exception, ex:
                form = LoginForm()
                return direct_to_template(request, 'texas/error.html',
                        {'message': "Could not reset password\n%s" % ex})
        else: # login_is_new is 0 or something else
            user = authenticate(username=request.POST['username'],
                    password=request.POST['password'])
            if user is not None:
                if user.is_active:
                    ip_address = request.META['REMOTE_ADDR']
                    do_process_requests(ip_address, user)
                    login(request, user)
                    return redirect_to(request, '/buy/purchases/')
                else:
                    #return direct_to_template(request, 'registration/inactive_account.html')
                    form = LoginForm()
                    message = "Your account is not active."
                    return direct_to_template(request,
                            'registration/login.html',
                            {'form': form, 'message': message})
            else:
                #return direct_to_template(request, 'registration/invalid_login.html')
                form = LoginForm()
                message = "Invalid credentials."
                return direct_to_template(request, 'registration/login.html',
                        {'form': form, 'message': message})
    else:
        form = LoginForm()
        return direct_to_template(request, 'registration/login.html', {'form':
                form})

def user_confirm(request, user_id, code):
    try:
        user = User.objects.get(pk=user_id)
        if user.first_name and user.first_name == code:
            user.is_active = 1
            user.first_name = ''
            user.save()

            form = LoginForm()
            message = "Account confirmed, please login to continue."
            return direct_to_template(request, 'registration/login.html',
                    {'form': form, 'message': message})
        elif not user.first_name:
            form = LoginForm()
            message = "Account has already been confirmed, please log in."
            return direct_to_template(request, 'registration/login.html',
                    {'form': form, 'message': message})
        else:
            return direct_to_template(request, 'texas/error.html',
                    {'message': 'Invalid confirmation.'})
    except:
        return direct_to_template(request, 'texas/error.html',
                {'message': 'Confirmation error.'})

def user_logout(request):
    logout(request)
    return redirect_to(request, '/')

def user_profile(request):
    return direct_to_template(request, 'registration/profile.html')
