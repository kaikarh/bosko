import json, re

from django import forms

from .models import Release, Link, AlbumPost


class BootstrapStyledForm(forms.ModelForm):
    error_css_class = 'alert alert-warning'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # skip boolean field
            if isinstance(field, forms.fields.BooleanField): continue                
            field.widget.attrs.update({'class': 'form-control'})
    
    def __getitem__(self, name):
        # rewrite the getitem implementation to add extra class for label
        boundfield = super().__getitem__(name)
        boundfield.label_tag = self.label_tag_with_form_label_class(boundfield.label_tag)
        return boundfield

    def label_tag_with_form_label_class(self, f):
        def inner(contents=None, attrs=None, label_suffix=None):
            if not attrs: attrs = {}
            attrs.update({'class': 'form-label'})
            return f(contents, attrs, label_suffix)
        return inner

    def as_div(self):
        # Return this form rendered as HTML <div>s.
        return self._html_output(
            normal_row='<div%(html_class_attr)s>%(errors)s%(label)s %(field)s%(help_text)s</div>',
            error_row='<div>%s</div>',
            row_ender='</div>',
            help_text_html=' <span class="helptext">%s</span>',
            errors_on_separate_row=False,
        )

class ReleaseForm(BootstrapStyledForm):
    class Meta:
        model = Release
        fields = ['release_name', 'archive_name', 'archive_size',
                  'stream_song_name', 'stream_song_url', 'adam_id',  'posted', 'post_url']

class AlbumPostForm(BootstrapStyledForm):
    release_date = forms.CharField(required=False)
    tracks = forms.CharField(required=False, widget=forms.Textarea)
    class Meta:
        model = AlbumPost
        fields = '__all__'

    def clean_release_date(self):
        data = self.cleaned_data['release_date']
        if len(data) == 4:
            data = f'{data}-01-01'
        return data

    def clean_tracks(self):
        # Tracks field accepts various data format
        # Clean all data to python list
        def format_tracks(tracks_list):
            tracks = []
            for t in tracks_list:
                if t:
                    tracks.append({'name': t})
            return tracks

        tracks_string = self.cleaned_data['tracks']
        try:
            tracks = json.loads(tracks_string)
        except ValueError as err:
            # Comma seperated track names
            if not tracks_string.count('\n'):
                # Single line, comma seperated track string
                tracks = tracks_string.split(',')
            else:
                # bootcamp filter
                # Filters "trackname 00:00"
                exp = re.compile(r"([\w\(\)\ \.\&\’\/\[\]]+)(?:\W\d+:\d+)")
                # simple filter
                #exp = re.compile(r"\ ([a-zA-Z\ ]+)")
                tracks = exp.findall(tracks_string)
            return format_tracks(tracks)
        # its json
        # pass it to model to continue validate
        return tracks

LinkInlineFormSet = forms.inlineformset_factory(
    Release,
    Link,
    fields=('url', 'passcode'),
    form=BootstrapStyledForm,
    extra=1
)