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
    return direct_to_template(request, 'txadmin/index.html')
