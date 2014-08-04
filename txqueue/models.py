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
from django.db import models
from datetime import datetime

# Create your models here.
class Reservation(models.Model):
    code = models.CharField(max_length=10)
    ip_address = models.CharField(max_length=15)
    is_ready = models.BooleanField(default=False)
    reserved = models.DateTimeField()
    active = models.DateTimeField()
    started = models.DateTimeField(null=True, blank=True)
    finished = models.DateTimeField(null=True, blank=True)

class Setting(models.Model):
    setting = models.CharField(max_length=10)
    value = models.CharField(max_length=255)

    def __unicode__(self):
        return "%s: %s" % (self.setting, self.value)
