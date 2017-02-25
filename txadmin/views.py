from django.http import HttpResponse
from django.views.generic.simple import direct_to_template, redirect_to
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from tickets.texas.models import *
from tickets.txsched.models import *
from datetime import datetime
from datetime import timedelta
import time
from django.contrib.auth.models import User

def index(request):
    occurrences = Occurrence.objects.filter(
            event__admins=request.user).order_by('-end_date')
    occurrences_old = occurrences.filter(end_date__lt=datetime.now())
    occurrences_active = occurrences.filter(end_date__gte=datetime.now())
    return direct_to_template(request, 'txadmin/index.html', {
            'occurrences_active': occurrences_active,
            'occurrences_old': occurrences_old
        })

def occurrence_stats(request, occurrence_id):
    occurrence = get_object_or_404(Occurrence, pk=occurrence_id)
    if not request.user in occurrence.event.admins.all():
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or lacking admin privileges"})

    tickets = Ticket.objects.filter(purchase__occurrence=occurrence,
            purchase__status='P')

    return direct_to_template(request,
            'txadmin/occurrence/stats.html',
            {'occurrence': occurrence, 'tickets': tickets })

def occurrence_purchases(request, occurrence_id):
    occurrence = get_object_or_404(Occurrence, pk=occurrence_id)
    if not request.user in occurrence.event.admins.all():
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or lacking admin privileges"})

    purchases = Purchase.objects.filter(occurrence=occurrence)

    return direct_to_template(request,
            'txadmin/occurrence/purchases.html',
            {'occurrence': occurrence, 'purchases': purchases })

def purchase_delete(request, purchase_id):
    purchase = get_object_or_404(Purchase, pk=purchase_id)
    if not request.user in purchase.occurrence.event.admins.all():
        return direct_to_template(request, 'texas/error.html',
            {'message': "Not logged in or lacking admin privileges"})
    purchase.status = 'D'
    purchase.save()

    return redirect_to(request,
            '/a/occurrence/%i/purchases/' % purchase.occurrence_id)
