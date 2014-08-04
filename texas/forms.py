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
from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(label='Email Address', max_length=75)
    password = forms.CharField(widget=forms.PasswordInput(render_value=False))

class SaleForm(forms.Form):
    tickets = forms.CharField(label='Number of Tickets', max_length=2)
    name = forms.CharField(label='Full Name', max_length=50)
    email = forms.CharField(label='Email', max_length=75)
