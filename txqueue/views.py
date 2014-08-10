"""
    TXQueue Ticket Queue
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

from django.db.models import Sum
from django.views.generic.simple import direct_to_template, redirect_to
from django.shortcuts import redirect
from tickets.txqueue.models import Reservation, QueuedTier, ChatMessage
from random import Random, choice, randint
from datetime import datetime, timedelta
from django.conf import settings
import time
from ponies import PONIES
import string

def index(request):
    tier = None
    try:
        tier = QueuedTier.objects.exclude(
                ends__lte=datetime.now()).order_by('starts')[0]
    except:
        return direct_to_template(request, 'txqueue/index.html')

    # get reservation
    res = None
    try:
        # first from url
        res = Reservation.objects.get(queued_tier=tier,
                code__exact=request.GET.get('code', None),
                finished__isnull=True)
        if res.finished:
            res = None
    except:
        pass
    try:
        # then from cookie
        if not res and 'code' in request.COOKIES:
            res = Reservation.objects.get(queued_tier=tier,
                    code__exact=request.COOKIES['code'], finished__isnull=True)
        if res.finished:
            res = None
    except:
        pass
    try:
        # then from ip address
        if not res:
            res = Reservation.objects.get(queued_tier=tier,
                    ip_address=request.META['REMOTE_ADDR'],
                    finished__isnull=True)
        if res.finished:
            res = None
    except:
        pass

    if res and 'message' in request.POST and 'nick' in request.POST:
        if (res.nick != request.POST['nick']):
            res.nick = request.POST['nick']
            res.save()
        if len(request.POST['message']) > 0:
            message = ChatMessage(reservation=res,
                    message = request.POST['message'],
                    stamp = datetime.now())
            message.save()
        return redirect('/q/?code=%s#chat' % (res.code))
    chatmessages = ChatMessage.objects.order_by('-stamp')[:10]

    if tier.starts > datetime.now():
        # queue has not started
        starts_in = tier.starts - datetime.now()
        if starts_in < timedelta(hours=1) and not res:
            # hand out an early reservation
            res = Reservation(
                    queued_tier=tier,
                    code=''.join(Random().sample(string.letters+string.digits,
                    10)), ip_address=request.META['REMOTE_ADDR'])
            reserved = tier.starts
            reserved -= timedelta(seconds=reserved.second)
            reserved += timedelta(seconds=randint(0, 59))
            res.reserved = reserved
            res.active = datetime.now()
            res.user_agent = request.META['HTTP_USER_AGENT']
            res.nick = res.ip_address
            res.save()

        starts = tier.starts + timedelta(minutes=1)
        pony = choice(PONIES)
        response = direct_to_template(request, 'txqueue/index.html', {
            "pony": pony, "starts": starts, "tier": tier,
            "reservation": res, "chatmessages": chatmessages})
        if res:
            # set reservation cookie
            max_age = max_age = 24*60*60
            expires = datetime.strftime(
                    datetime.utcnow() + timedelta(seconds=max_age),
                    "%a, %d-%b-%Y %H:%M:%S GMT")
            response.set_cookie('code', res.code, max_age=max_age,
                    expires=expires)
        return response

    if not res:
        # otherwise get a new one
        res = Reservation(
                queued_tier=tier,
                code=''.join(Random().sample(string.letters+string.digits,
                10)), ip_address=request.META['REMOTE_ADDR'])
        reserved = datetime.now()
        reserved -= timedelta(seconds=reserved.second)
        reserved += timedelta(seconds=randint(0, 59))
        res.user_agent = request.META['HTTP_USER_AGENT']
        res.nick = res.ip_address
        res.reserved = reserved

    # set activity
    """
    pony = None
    too_recent = timedelta(seconds=10)
    if not res.active or datetime.now() - res.active > too_recent:
        # pick a pony
        pony = choice(PONIES)
    """
    pony = choice(PONIES)
    agent_warning = request.META['HTTP_USER_AGENT'] != res.user_agent
    res.active = datetime.now()
    res.user_agent = request.META['HTTP_USER_AGENT']
    res.save()

    # get stats
    queue_expired_before = datetime.now() - timedelta(minutes=15)
    active_expired_before = datetime.now() - timedelta(minutes=30)
    # get number active in the system (started, but not finished)
    active = Reservation.objects.filter(queued_tier=tier)\
            .exclude(started__isnull=True)\
            .exclude(finished__isnull=False)\
            .exclude(active__lt=active_expired_before)\
            .count()
    # get everyone in the queue (not started)
    queue = Reservation.objects.filter(queued_tier=tier, started__isnull=True)\
            .exclude(active__lt=queue_expired_before)
    in_queue = queue.count()
    # get count ahead of this user
    ahead = queue.exclude(reserved__gt=res.reserved).count()

    if active < tier.max_active:
        # the active list has open spots
        ready_count = tier.max_active - active
        ready = queue.order_by('reserved', 'id')[:ready_count]
        if res in ready:
            res.is_ready = 1
            res.save()
            update_stats(res.queued_tier)

    since_start = datetime.now() - res.reserved
    min_since = timedelta(minutes=1)
    is_started = False
    wait_message = ""
    if since_start > min_since:
        is_started = True
    else:
        wait_message = choice([
            "reticulating pony splines ...",
            "queueing hippies ...",
            "herding cats ...",
            "galloping into the queue ...",
            "analyzing mud ...",
            "waking the neighbors ...",
            "drawing ASCII ponies ...",
            "gathering rain clouds ...",
            "cleaning off playa dust ...",
            "applying zombie makeup ...",
            "kicking out sneak-ins ...",
            "getting greeters drunk ...",
            "bothering rangers ...",
            "waking up board members ...",
            "revving harleys ...",
        ])

    return_url = settings.QUEUE_RETURN_URL
    response = direct_to_template(request, 'txqueue/index.html',
            {"reservation": res, "active": active, "in_queue": in_queue,
                "ahead": ahead, "pony": pony, "return_url": return_url,
                "is_started": is_started, "since_start": since_start,
                "wait_message": wait_message, "tier": tier,
                "agent_warning": agent_warning, "chatmessages": chatmessages})

    # set reservation cookie
    max_age = max_age = 24*60*60
    expires = datetime.strftime(
            datetime.utcnow() + timedelta(seconds=max_age),
            "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie('code', res.code, max_age=max_age, expires=expires)
    return response

def check_code(request, code):
    try:
        reservation = Reservation.objects.get(code__exact=code)
        if reservation and reservation.is_ready and not reservation.finished:
            reservation.started = datetime.now()
            reservation.save()
            update_stats(reservation.queued_tier)
            return direct_to_template(request, 'txqueue/return.txt', {'code':
                1})
        else:
            return direct_to_template(request, 'txqueue/return.txt', {'code':
                0})
    except:
        return direct_to_template(request, 'txqueue/return.txt', {'code': 0})

def use_code(request, code):
    try:
        tix = request.GET.get('tix', None)
        reservation = Reservation.objects.get(code__exact=code)
        if reservation and reservation.is_ready and not reservation.finished:
            reservation.finished = datetime.now()
            reservation.tickets = tix
            reservation.save()
            update_stats(reservation.queued_tier)
            return direct_to_template(request, 'txqueue/return.txt',
                    {'code': 1})
        else:
            return direct_to_template(request, 'txqueue/return.txt', {'code':
                0})
    except:
        return direct_to_template(request, 'txqueue/return.txt', {'code': 0})

def pay_code(request, code):
    try:
        reservation = Reservation.objects.get(code__exact=code)
        if reservation and reservation.is_ready and not reservation.paid:
            reservation.paid = datetime.now()
            reservation.save()
            update_stats(reservation.queued_tier)
            return direct_to_template(request, 'txqueue/return.txt',
                    {'code': 1})
        else:
            return direct_to_template(request, 'txqueue/return.txt', {'code':
                0})
    except:
        return direct_to_template(request, 'txqueue/return.txt', {'code': 0})

def update_stats(tier):
    tier.ticket_count_paid = tier.reservation_set.filter(
            paid__isnull=False).aggregate(Sum('tickets'))['tickets__sum']
    if tier.ticket_count_paid:
        tier.average_tickets = float(tier.ticket_count_paid) /\
                float(tier.reservation_set.filter(paid__isnull=False).count())
    else:
        tier.ticket_count_paid = 0
        tier.average_tickets = 1
    tier.ticket_count_ready = tier.reservation_set.filter(is_ready=1).exclude(
            started__isnull=False).count() * tier.average_tickets
    tier.ticket_count_started = tier.reservation_set.filter(
            started__isnull=False).exclude(
            finished__isnull=False).count() * tier.average_tickets
    tier.ticket_count_finished = tier.reservation_set.filter(
            finished__isnull=False).exclude(
            paid__isnull=False).count() * tier.average_tickets
    tier.save()
