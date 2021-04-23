from django import forms

from .models import Release

# custom widget with datalist
class ListTextWidget(forms.TextInput):
    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.attrs.update({'list':'list__%s' % self._name})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name
        for item in self._list:
            data_list += '<option value="%s">' % item
        data_list += '</datalist>'

        return (text_html + data_list)

class AplForm(forms.Form):
    apple_music_url = forms.URLField(widget=forms.URLInput(attrs={'class': 'form-control'}), required=False)
    baidu_share = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)

class PostForm(forms.Form):
    artist = forms.CharField()
    title = forms.CharField()
    genre = forms.CharField(required=False)
    artwork = forms.URLField(required=False)
    year = forms.CharField(max_length=4, required=False)
    rip_info = forms.CharField(required=False)
    arc_info = forms.CharField(required=False)
    hidden_info = forms.CharField(required=False)
    stream_url = forms.URLField(required=False)
    download_link = forms.URLField(required=False)
    download_passcode = forms.CharField(max_length=4, required=False)
    description = forms.CharField(widget=forms.Textarea, required=False)
    tracks = forms.CharField(widget=forms.Textarea, required=False)
    apple_tracks = forms.CharField(widget=forms.Textarea(attrs={'readonly':'readonly'}), required=False)

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)

        datalist = {
            'rip_info_options': ['web / scene / mp3 320K',
                                 'CD / scene / mp3 v0',
                                 'CD / scene / flac',
                                 'vinyl / scene / flac',
                                 'tape / scene / mp3'],
            'arc_info_options': ['zip / password protected',
                                 'rar'],
            'hidden_info_options': ['密码：needpop.com',
                                    'Password: needpop.com',],
        }

        # datalist fields
        self.fields['rip_info'].widget = ListTextWidget(datalist['rip_info_options'], 'rip-info-list')
        self.fields['arc_info'].widget = ListTextWidget(datalist['arc_info_options'], 'arc-info-list')
        self.fields['hidden_info'].widget = ListTextWidget(datalist['hidden_info_options'], 'hidden-info-list')

        # bootstrap pretty form
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class ReleaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ReleaseForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = Release
        fields = ['release_name', 'archive_name', 'archive_size',
                  'stream_song_name', 'stream_song_url', 'share_link',
                  'share_link_passcode', 'adam_id',  'post_url']
