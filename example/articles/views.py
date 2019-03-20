from django.http.response import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from users.views import SwitchUserMixin

from .models import Article
from .signals import article_viewed


class ArticleListView(SwitchUserMixin, ListView):

    model = Article


class ArticleCreateView(CreateView):

    model = Article
    fields = ('title', 'text')

    def form_valid(self, form):
        article = form.save(commit=False)
        article.author = self.request.user
        article.save()
        return HttpResponseRedirect('/')


class ArticleUpdateView(UpdateView):

    model = Article
    fields = ('title', 'text')
    success_url = reverse_lazy('article_list')

    def get(self, request, *args, **kwargs):
        article = self.get_object()
        if article.author != request.user:
            article_viewed.send(self.__class__, user=request.user, article=article)
        return super().get(request, *args, **kwargs)
