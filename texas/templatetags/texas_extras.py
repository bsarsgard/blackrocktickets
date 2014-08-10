from django import template
from django.contrib.auth.models import User
from tickets.texas.models import *
from datetime import datetime

register = template.Library()

def do_get_order_count(parser, token):
    try:
        tag_name, user = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires 1 argument" % token.contents.split()[0]
    return GetOrderCountNode(user)
register.tag('get_order_count', do_get_order_count)

def do_get_ticket_count(parser, token):
    try:
        tag_name, user = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires 1 argument" % token.contents.split()[0]
    return GetTicketCountNode(user)
register.tag('get_ticket_count', do_get_ticket_count)

def do_get_payment_url(parser, token):
    try:
        tag_name, purchase = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires 1 argument" % token.contents.split()[0]
    return GetPaymentUrlNode(purchase)
register.tag('get_payment_url', do_get_payment_url)

class GetPaymentUrlNode(template.Node):
    def __init__(self, purchase):
        self.purchase = template.Variable(purchase)

    def render(self, context):
        purchase = self.purchase.resolve(context)
        try:
            return purchase.get_paypal_url()
        except:
            return "#"

#@register.tag(name="list_purchases")
def do_list_purchases(parser, token):
    try:
        tag_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires no arguments" % token.contents.split()[0]
    return ListPurchasesNode()
register.tag('list_purchases', do_list_purchases)

class GetOrderCountNode(template.Node):
    def __init__(self, user):
        self.user = template.Variable(user)

    def render(self, context):
        request = context['request']
        user = self.user.resolve(context)
        count = Purchase.objects.filter(
                user=user
        ).exclude(
                status='D'
        ).exclude(
                status='T', expiration_date__lte=datetime.now()
        ).exclude(
                occurrence__end_date__lte=datetime.now()
        ).count()
        if count > 0:
            return "<span class=\"badge\">%i</span>" % count
        else:
            return ""

class GetTicketCountNode(template.Node):
    def __init__(self, user):
        self.user = template.Variable(user)

    def render(self, context):
        request = context['request']
        user = self.user.resolve(context)
        count = Ticket.objects.filter(
                assigned_user=user, purchase__status='P'
        ).exclude(
                purchase__occurrence__end_date__lte=datetime.now()
        ).count()
        paid_purchases = Purchase.objects.filter(
                user=user, status='P'
        ).exclude(
                occurrence__end_date__lte=datetime.now()
        )
        for purchase in paid_purchases:
            count += purchase.ticket_set.count()
        if count > 0:
            return "<span class=\"badge\">%i</span>" % count
        else:
            return ""

class ListPurchasesNode(template.Node):
    def render(self, context):
        request = context['request']
        user = request.user
        purchase_list = ""
        if user.is_authenticated():
            # Get any tentative purchases
            purchases = Purchase.objects.filter(
                    user=user, status='T'
            ).exclude(
                    expiration_date__lte=datetime.now()
            )
            for purchase in purchases:
                expires = (purchase.expiration_date - datetime.now()) / 60
                status = purchase.get_status_display()
                purchase_list += "<div class=\"alert alert-warning\">"
                purchase_list += "<h4>Order expiring in: <span class=\"badge countdown\">%s</span> minutes</h4>" % expires.seconds
                purchase_list += "<span class=\"label label-primary\">%s</span> - %i ticket(s)" % (status, purchase.ticket_set.count())
                purchase_list += "<a href=\"/buy/purchases/\" class=\"btn btn-success btn-sm pull-right\">List purchases and pay</a>"
                purchase_list += "</div>"
        else:
            purchase_list += "<div class=\"alert alert-info dismissable\">"
            purchase_list += "<h4>You are not logged in</h4>"
            purchase_list += "<p><a href=\"/login/\">Click here to log in or create a new account</a></p>"
            purchase_list += "</div>"
            ip_address = request.META['REMOTE_ADDR']
            purchase_requests = PurchaseRequest.objects.filter(
                    ip_address=ip_address
            ).exclude(
                    purchase__isnull=False
            ).exclude(
                    expiration_date__lte=datetime.now()
            )
            for purchase_request in purchase_requests:
                expires = (purchase_request.expiration_date - datetime.now()) / 60
                status = 'Requested'
                purchase_list += "<div class=\"alert alert-danger\">"
                purchase_list += "<h4>Order expiring in: <span class=\"badge countdown\">%s</span></h4>" % expires.seconds
                purchase_list += "<span class=\"label label-primary\">%s</span> - %i ticket(s)" % (status, purchase_request.tickets_requested)
                purchase_list += "<a href=\"/buy/purchases/\" class=\"btn btn-success btn-sm pull-right\">Login to complete purchase</a>"
                purchase_list += "</div>"

        return purchase_list

#@register.tag(name="chart")
def do_chart(parser, token):
    try:
        tag_name, style, size, rows = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires three arguments" \
            % token.contents.split()[0]
    return ChartNode(style, size, rows)
register.tag('chart', do_chart)

class ChartNode(template.Node):
    def __init__(self, style, size, rows):
        self.style = style
        self.size = size
        self.rows = template.Variable(rows)

    def render(self, context):
        try:
            rows = self.rows.resolve(context)
            values = [hit[1] for hit in rows]
            labels = [hit[0] for hit in rows]

            style = self.style[1:-1]
            size = self.size[1:-1]

            return self.get_chart(style, size, values, labels)
        except template.VariableDoesNotExist:
            return "No chart data";

    def get_chart(self, style, size, values, labels):
        if style == "p3":
            value_str = ""
            label_str = ""
            for ii in range(len(values)):
                value_str += "%s," % values[ii]
                label_str += "%s (%s)|" % (labels[ii], values[ii])

            values = value_str[:-1]
            labels = label_str[:-1]
            #colors = 'dd0000,ffa500,eeee00,008000,0000dd,4b0082,ee82ee'
            colors = 'add64e,e8a04d,56c5eb'

            return "<img src=\"http://chart.apis.google.com/chart?cht=%s&chco=%s&chd=t:%s&chs=%s&chl=%s\" alt=\"Chart\" />" % (style, colors, values, size, labels)
        elif style == "lc":
            value_str = ""
            label_str = ""
            range_str = ""
            value_min = 0
            value_max = 0
            for ii in range(len(values)):
                if values[ii] < value_min:
                    value_min = int(values[ii])
                if values[ii] > value_max:
                    value_max = int(values[ii])
                value_str += "%s," % values[ii]
                label_str += "%s|" % labels[ii]

            values = value_str[:-1]
            labels = label_str[:-1]
            ranges = ""

            num_samples = min(10, abs(value_max - value_min) + 1)

            if num_samples > 1:
                samples, step = numpy.linspace(value_min, value_max,
                        num=num_samples, retstep=True)

                for ii in samples:
                    range_str += "%i|" % ii
                value_max += step
                ranges = "%s%i" % (range_str, value_max)

            return "<img src=\"http://chart.apis.google.com/chart?cht=%s&chco=1f8ec8&chd=t:%s&chds=%s,%s&chs=%s&chxt=y,x&chxl=1:|%s|0:|%s&chm=N,000000,0,-1,11,1\" alt=\"Chart\" />" % (style, values, value_min, value_max, size, labels, ranges)
        elif style == "bhs":
            value_str = ""
            label_str = ""
            range_str = ""
            value_min = 0
            value_max = 0
            for ii in range(len(values)):
                if values[ii] < value_min:
                    value_min = int(values[ii])
                if values[ii] > value_max:
                    value_max = int(values[ii])
                value_str += "%s," % values[ii]
                label_str = "%s|%s" % (labels[ii], label_str)

            values = value_str[:-1]
            labels = label_str[:-1]
            ranges = ""

            num_samples = min(10, abs(value_max - value_min) + 1)

            if num_samples > 1:
                samples, step = numpy.linspace(value_min, value_max,
                        num=num_samples, retstep=True)

                for ii in samples:
                    range_str += "%i|" % ii
                value_max += step
                ranges = "%s%i" % (range_str, value_max)

            return "<img src=\"http://chart.apis.google.com/chart?cht=%s&chco=1f8ec8&chd=t:%s&chds=%s,%s&chs=%s&chxt=y,x&chxl=0:|%s|1:|%s&chm=N ,000000,0,-1,11,1&chbh=15\" alt=\"Chart\" />" % (style, values, value_min, value_max, size, labels, ranges)

@register.filter(name='addcss')
def addcss(value, arg):
    return value.as_widget(attrs={'class': arg})
