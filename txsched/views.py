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
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from tickets.texas.models import *
from tickets.txsched.models import *
from datetime import datetime
from datetime import timedelta
import time
from django.contrib.auth.models import User
#from tickets.txsched.helpers import Slot

def index(request):
    sign_ups = SignUp.objects.filter(occurrence__end_date__gte=datetime.now(),
            start_date__lte=datetime.now())
    latest_signups = SignUp.objects.latest('start_date')
    
    return direct_to_template(request, 'txsched/index.html', {'sign_ups':
            sign_ups, 'latest_signups': latest_signups})

def sign_up_admin(request, sign_up_id):
    sign_up = get_object_or_404(SignUp, pk=sign_up_id)
    latest_signups = SignUp.objects.latest('start_date')
    
    return direct_to_template(request, 'txsched/sign_up_admin.html',
            {'sign_up': sign_up, 'latest_signups': latest_signups})

def schedule(request, schedule_id, sign_up_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    sign_up = get_object_or_404(SignUp, pk=sign_up_id)
  
    if request.POST.get('sign_up_position', None):
        # signing up for a position
        position = get_object_or_404(Position,
                pk=request.POST['sign_up_position'])
        start_date = datetime(*time.strptime(request.POST['sign_up_start'],
                '%Y-%m-%d %H:%M')[:5])
        end_date = datetime(*time.strptime(request.POST['sign_up_end'],
                '%Y-%m-%d %H:%M')[:5])
        nick_name = request.POST.get('nick_name', '')
        label = request.POST.get('label', '')
        description = request.POST.get('description', '')
        try:
            profile = request.user.get_profile()
        except:
            profile = UserProfile(user=request.user)
        profile.nick_name = nick_name
        profile.save()

        shift = Shift(position=position, user=request.user,
                occurrence=sign_up.occurrence, start_date=start_date,
                end_date=end_date)

        if label:
            shift.label = label
        else:
            shift.label = nick_name
        if description:
            shift.description = description

        shift.save()
        return redirect_to(request, reverse('schedule', args=[schedule_id,
                sign_up_id]))
    elif request.POST.get('remove_position', None):
        # removing a signed up position
        position = get_object_or_404(Position,
                pk=request.POST['remove_position'])
        start_date = request.POST['remove_time']
        try:
            shifts = Shift.objects.filter(position=position, user=request.user,
                    occurrence=sign_up.occurrence, start_date__lte=start_date,
                    end_date__gt=start_date)
            for shift in shifts:
                shift.delete()
        except:
            pass
        return redirect_to(request, reverse('schedule', args=[schedule_id,
                sign_up_id]))
    else:
        # display the schedule
        positions = schedule.get_positions().filter(parent__isnull=True)
        latest_signups = SignUp.objects.latest('start_date')

        slots = []

        start = sign_up.occurrence.start_date + timedelta(
                minutes=schedule.start_offset)
        end = sign_up.occurrence.end_date + timedelta(
                minutes=schedule.end_offset)
        current = start
        last_day = ''
        while current < end:
            slot = {'schedule': schedule, 'sign_up': sign_up,
                    'start_date': current, 'positions': []}
            block_delta = current - start
            current_blocks = block_delta.days * 24 * 60 / schedule.block_size
            current_blocks += block_delta.seconds / 60 / schedule.block_size

            day = current.strftime('%A')
            #day = current_blocks
            if day != last_day:
                # print header at start of each new day
                slot['header'] = day
                last_day = day

            for position in positions:
                child_positions = Position.objects.all().filter(parent=position)
                # check child positions to substitute
                for child in child_positions:
                    child_black_outs = BlackOut.objects.filter(
                            position=child,
                            start_block__lte=current_blocks,
                            end_block__gt=current_blocks)
                    if not child_black_outs:
                        # open child position; use it instead
                        position = child
                        break
                shift_end = None
                shift_length = None
                if (current_blocks - position.shift_offset) \
                        % position.shift_length == 0:
                    # this position has a start in this slot
                    shift_end = current + timedelta(minutes=(
                            schedule.block_size * position.shift_length))
                    shift_length = position.shift_length
                if (current == start and position.shift_offset <= 0):
                    # handle partial starting shifts
                    shift_end = current + timedelta(
                            minutes=(schedule.block_size * (
                            position.shift_length + position.shift_offset)))
                    shift_length = position.shift_length + \
                            position.shift_offset
                # check for black-outs
                black_outs = BlackOut.objects.filter(position=position,
                        start_block__lte=current_blocks,
                        end_block__gt=current_blocks)
                if shift_end or black_outs:
                    # need to start a shift in this slot
                    shifts = None
                    users = None
                    shift_open = sign_up.end_date > datetime.now()
                    if black_outs:
                        # a blackout is active during this shift
                        if position.parent:
                            # blackouts are used in child shifts to yeild
                            shift_length = 0
                        else:
                            shift_length = 0
                            for black_out in black_outs:
                                if black_out.start_block == current_blocks:
                                    black_out_length = black_out.end_block - \
                                            black_out.start_block
                                    if black_out_length > shift_length:
                                        shift_length = black_out_length
                    else:
                        # check if a blackout starts mid-shift
                        pblack_outs = BlackOut.objects.filter(position=position,
                                start_block__lt=current_blocks + shift_length,
                                end_block__gt=current_blocks + shift_length)
                        for black_out in pblack_outs:
                            if black_out.start_block < current_blocks +\
                                    shift_length:
                                shift_length = black_out.start_block -\
                                    current_blocks
                                shift_end = current + timedelta(minutes=(
                                    schedule.block_size * shift_length))
                        
                        shifts = Shift.objects.filter(position=position,
                                occurrence=sign_up.occurrence,
                                start_date__gte=current,
                                end_date__lte=shift_end)
                        if len(shifts) >= position.max_users:
                            shift_open = False
                        for shift in shifts:
                            if request.user == shift.user:
                                shift_open = False
                    if shift_length > 0:
                        slot['positions'].append({'position_id': position.id,
                                'blocks': shift_length, 'shifts': shifts,
                                'max_users': position.max_users,
                                'shift_end': shift_end,
                                'black_outs': black_outs,
                                'detail_required': position.detail_required,
                                'shift_open': shift_open})
            slots.append(slot)
            current += timedelta(minutes=schedule.block_size)

        return direct_to_template(request, 'txsched/schedule.html',
                {'schedule': schedule, 'sign_up': sign_up, 'slots': slots, 'latest_signups': latest_signups})

