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
from tickets.texas.models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms

class UserForm( forms.ModelForm ):
    class Meta:
        model= User
        username = forms.EmailField(max_length=75,
            help_text = "The person's email address.")

class UserAdminOverride( UserAdmin ):
    form= UserForm
    list_display = ( 'email', 'first_name', 'last_name', 'is_staff' )
    list_filter = ( 'is_staff', )
    search_fields = ( 'email', )

class PurchaseModel(admin.ModelAdmin):
    search_fields = ('user__email',)
    list_filter = ('status',)

class ReservationModel(admin.ModelAdmin):
    search_fields = ('email',)

class EventAdmin(admin.ModelAdmin):
    filter_horizontal = ('admins',)


admin.site.unregister( User )
admin.site.register( User, UserAdminOverride )

admin.site.register(UserProfile)
admin.site.register(Event, EventAdmin)
admin.site.register(Occurrence)
admin.site.register(Tier)
admin.site.register(Coupon)
admin.site.register(PurchaseRequest)
admin.site.register(Purchase, PurchaseModel)
admin.site.register(Ticket)
admin.site.register(Payment)
admin.site.register(Reservation, ReservationModel)
admin.site.register(Comp)
admin.site.register(Option)
