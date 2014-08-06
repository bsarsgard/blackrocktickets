from django import template

#Django template custom math filters
#Ref : https://code.djangoproject.com/ticket/361
register = template.Library()

def mult(value, arg):
    "Multiplies the arg and the value"
    return int(value) * int(arg)

def sub(value, arg):
    "Subtracts the arg from the value"
    return int(value) - int(arg)

def div(value, arg):
    "Divides the value by the arg"
    return int(float(value) / float(arg))

def pct(value, arg):
    "Percent of value divided by the arg"
    return int(float(value) / float(arg) * 100.0)

def rpct(value, arg):
    "Reverse of Percent of value divided by the arg"
    return int(float(arg - value) / float(arg) * 100.0)

register.filter('mult', mult)
register.filter('sub', sub)
register.filter('div', div)
register.filter('pct', pct)
register.filter('rpct', rpct)
