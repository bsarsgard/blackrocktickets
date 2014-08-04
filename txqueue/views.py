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

from django.views.generic.simple import direct_to_template, redirect_to
from tickets.txqueue.models import Reservation, Setting
from random import Random, choice, randint
from datetime import datetime, timedelta
from django.conf import settings
import time
from ponies import PONIES
import string

def index(request):
    starts = datetime(*time.strptime(
            Setting.objects.get(setting__exact='starts').value,
            "%Y-%m-%d %H:%M:%S")[:5])

    # get reservation
    res = None
    try:
        # first from url
        res = Reservation.objects.get(code__exact=request.GET.get('code',
                None), finished__isnull=True)
        if res.finished:
            res = None
    except:
        pass
    try:
        # then from cookie
        if not res and 'code' in request.COOKIES:
            res = Reservation.objects.get(code__exact=request.COOKIES['code'],
                    finished__isnull=True)
        if res.finished:
            res = None
    except:
        pass
    try:
        # then from ip address
        if not res:
            res = Reservation.objects.get(
                    ip_address=request.META['REMOTE_ADDR'],
                    finished__isnull=True)
        if res.finished:
            res = None
    except:
        pass

    if starts > datetime.now():
        # queue has not started
        starts_in = starts - datetime.now()
        if starts_in < timedelta(hours=1) and not res:
            # hand out an early reservation
            res = Reservation(
                    code=''.join(Random().sample(string.letters+string.digits,
                    10)), ip_address=request.META['REMOTE_ADDR'])
            reserved = starts
            reserved -= timedelta(seconds=reserved.second)
            reserved += timedelta(seconds=randint(0, 59))
            res.reserved = reserved
            res.active = datetime.now()
            res.save()

        starts += timedelta(minutes=1)
        pony = choice(PONIES)
        response = direct_to_template(request, 'txqueue/index.html', {
            "pony": pony, "starts": starts})
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
                code=''.join(Random().sample(string.letters+string.digits,
                10)), ip_address=request.META['REMOTE_ADDR'])
        reserved = datetime.now()
        reserved -= timedelta(seconds=reserved.second)
        reserved += timedelta(seconds=randint(0, 59))
        res.reserved = reserved

    # set activity
    pony = None
    too_recent = timedelta(seconds=10)
    if not res.active or datetime.now() - res.active > too_recent:
        # pick a pony
        pony = choice(PONIES)
    res.active = datetime.now()
    res.save()

    # get stats
    queue_expired_before = datetime.now() - timedelta(minutes=15)
    max_active = int(Setting.objects.get(setting__exact='max_active').value)
    active_expired_before = datetime.now() - timedelta(minutes=30)
    # get number active in the system (started, but not finished)
    active = Reservation.objects.exclude(started__isnull=True)\
            .exclude(finished__isnull=False)\
            .exclude(active__lt=active_expired_before)\
            .count()
    # get everyone in the queue (not started)
    queue = Reservation.objects.filter(started__isnull=True)\
            .exclude(active__lt=queue_expired_before)
    in_queue = queue.count()
    # get count ahead of this user
    ahead = queue.exclude(reserved__gt=res.reserved).count()

    if active < max_active:
        # the active list has open spots
        ready_count = max_active - active
        ready = queue.order_by('reserved', 'id')[:ready_count]
        if res in ready:
            res.is_ready = 1
            res.save()

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
                "wait_message": wait_message})

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
            return direct_to_template(request, 'txqueue/return.txt', {'code':
                1})
        else:
            return direct_to_template(request, 'txqueue/return.txt', {'code':
                0})
    except:
        return direct_to_template(request, 'txqueue/return.txt', {'code': 0})

def use_code(request, code):
    try:
        reservation = Reservation.objects.get(code__exact=code)
        if reservation and reservation.is_ready and not reservation.finished:
            reservation.finished = datetime.now()
            reservation.save()
            return direct_to_template(request, 'txqueue/return.txt',
                    {'code': 1})
        else:
            return direct_to_template(request, 'txqueue/return.txt', {'code':
                0})
    except:
        return direct_to_template(request, 'txqueue/return.txt', {'code': 0})
