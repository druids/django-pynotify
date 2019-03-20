from django.contrib.auth import login
from django.contrib.auth.models import User


class SwitchUserMixin:

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_anonymous:
            to_user = 'Alice'
        else:
            to_user = request.GET.get('user')

        if to_user:
            login(request, User.objects.get(username=to_user))

        return super().dispatch(request, *args, **kwargs)
