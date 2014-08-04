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
from django.db import models
from django.contrib.auth.models import User
from tickets.texas.models import Event, Occurrence

class Schedule(models.Model):
    event = models.ForeignKey(Event)
    label = models.CharField(max_length=50)
    block_size = models.IntegerField() # block size, in minutes
    start_offset = models.IntegerField(default=0) # from event start in minutes
    end_offset = models.IntegerField(default=0) # from end in minutes
    reminder_email = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    admins = models.ManyToManyField(User)
    def get_positions(self):
        return self.position_set.order_by('sort', 'label').all()

    def __unicode__(self):
        return self.label

class Position(models.Model):
    schedule = models.ForeignKey(Schedule)
    label = models.CharField(max_length=50)
    shift_offset = models.IntegerField() # offset from event start in blocks
    shift_length = models.IntegerField() # shift length in blocks
    max_users = models.IntegerField()
    detail_required = models.BooleanField(default=False)
    parent = models.ForeignKey('self', blank=True, null=True)
    shifts = models.ManyToManyField(User, through='Shift')
    description = models.TextField(blank=True, null=True)
    sort = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.label

class BlackOut(models.Model):
    position = models.ForeignKey(Position)
    label = models.CharField(max_length=50, blank=True, null=True)
    start_block = models.IntegerField() # offset from event start in minutes
    end_block = models.IntegerField() # duration in minutes

    def __unicode__(self):
        return "%s, %i-%i: %s" % (self.position.__unicode__(), self.start_block,
                self.end_block, self.label)

class SignUp(models.Model):
    occurrence = models.ForeignKey(Occurrence)
    schedules = models.ManyToManyField(Schedule)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    admins = models.ManyToManyField(User)

    def __unicode__(self):
        return "%s: %s - %s" % (self.occurrence.__unicode__(), self.start_date,
                self.end_date)

class Shift(models.Model):
    position = models.ForeignKey(Position)
    user = models.ForeignKey(User)
    occurrence = models.ForeignKey(Occurrence)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    label = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "%s: %s" % (self.position.__unicode__(), self.start_date)
