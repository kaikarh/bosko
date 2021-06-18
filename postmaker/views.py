import logging

from django.urls import reverse_lazy
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views.generic import ListView, DetailView, FormView, TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Release, AlbumPost
from .forms import ReleaseForm, LinkInlineFormSet, AlbumPostForm

# Create your views here.

logger = logging.getLogger(__name__)

def main(request):
    return HttpResponse("This is the postmaker.")

class ReleaseList(ListView):
    model = Release
    paginate_by = 300

    def get_queryset(self):
        if self.kwargs.get('type'):
            if self.kwargs['type'].upper() == 'MP3':
                return Release.objects.exclude(release_name__contains='FLAC-')
            elif self.kwargs['type'].upper() == 'FLAC':
                return Release.objects.filter(release_name__contains='FLAC-')
            else:
                raise Http404
        return Release.objects.all()

class ReleaseDetailView(LoginRequiredMixin, DetailView):
    model = Release

class ReleaseEditView(LoginRequiredMixin, UpdateView):
    model = Release
    form_class = ReleaseForm
    template_name_suffix = '_update_form'

class ReleaseLinkEditView(LoginRequiredMixin, UpdateView):
    model = Release
    form_class = LinkInlineFormSet
    template_name_suffix = '_update_form'

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

class AlbumPostCreateView(FormView):
    form_class = AlbumPostForm
    template_name = 'postmaker/albumpost_create.html'
    success_url = reverse_lazy('postmaker:albumpost-result')

    def form_valid(self, form):
        # Save form to session
        self.request.session['album_post'] = form.cleaned_data
        return super().form_valid(form)

class ReleaseAlbumPostCreateView(SingleObjectMixin, AlbumPostCreateView):
    model = Release
    template_name = 'postmaker/release_albumpost_create.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        try:
            return self.object.generate_albumpost_values()
        except Exception:
            return self.initial.copy()

class AlbumPostResultView(TemplateView):
    template_name = 'postmaker/albumpost_result.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            album_post = AlbumPost(**self.request.session.pop('album_post'))
            album_post.clean()
        except KeyError:
            # No data was supplied to generate a result
            raise Http404
        context['rendered_post'] = album_post.render_post()
        context['meta'] = {
            'accounts': self.request.session.get('np_accounts'),
            'subject': album_post
        }
        return context
