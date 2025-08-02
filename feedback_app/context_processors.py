
from django.contrib.auth.models import Group

def is_admin(request):
    user = request.user
    return {'is_admin': user.is_superuser or user.groups.filter(name='admin').exists()}


def is_hod(request):
    return {'is_hod': request.user.groups.filter(name='hod').exists()}

def is_teacher(request):
    return {'is_teacher': request.user.groups.filter(name='teacher').exists()}

def is_principal(request):
    return {'is_principal': request.user.groups.filter(name='principal').exists()}