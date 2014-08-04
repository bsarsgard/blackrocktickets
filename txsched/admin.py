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
from tickets.txsched.models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms

class ScheduleAdmin(admin.ModelAdmin):
    filter_horizontal = ('admins',)

class SignupAdmin(admin.ModelAdmin):
    filter_horizontal = ('admins',)
    list_display = ('occurrence','start_date','end_date')

class ShiftAdmin(admin.ModelAdmin):
    list_display = ('position','start_date','user','label')
    list_filter = ['position']
    search_fields = ['user__email']
    date_hierarchy = 'start_date'

class BlackOutAdmin(admin.ModelAdmin):
    list_display = ('position','label', 'start_block','end_block')
    list_filter = ['position']
    search_fields = ['label']

class PositionAdmin(admin.ModelAdmin):
    list_display = ('label','schedule')
    list_filter = ['schedule']
  
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(SignUp, SignupAdmin)
admin.site.register(BlackOut, BlackOutAdmin)
