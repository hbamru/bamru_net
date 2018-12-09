from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_list_or_404, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView

from main.models import DataFile

import logging
logger = logging.getLogger(__name__)

class DataFileFormView(LoginRequiredMixin, CreateView):
    template_name = 'base_form.html'
    model = DataFile
    fields = ('file', 'caption', )

    def get_form(self, form_class=None):
        form = super(DataFileFormView, self).get_form(form_class)
        form.instance.member = self.request.user
        if 'file' in self.request.FILES:
            f = self.request.FILES['file']
            form.instance.name = f.name
            form.instance.size = f.size
            form.instance.content_type = f.content_type
            if '.' in f.name:
                form.instance.extension = f.name.split('.')[-1]
        return form

    def get_success_url(self, *args, **kwargs):
        return reverse('file_list')


class FileListView(LoginRequiredMixin, generic.ListView):
    template_name = 'file_list.html'
    context_object_name = 'file_list'

    def get_queryset(self):
        return DataFile.objects.order_by('name')


def download_data_file_helper(data_file):
    data_file.download_count += 1
    data_file.save()
    if settings.DEBUG:
        return redirect(data_file.file.url)
    response = HttpResponse()
    response['X-Accel-Redirect'] = data_file.file.url
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(
        data_file.name)
    return response

@login_required
def download_data_file_by_id_view(request, id):
    f = get_object_or_404(DataFile, id=id)
    return download_data_file_helper(f)

@login_required
def download_data_file_by_name_view(request, name):
    files = get_list_or_404(DataFile, name=name)
    f = files[0]  # TODO: Do we prefer the oldest or most recent?
    return download_data_file_helper(f)
