from rest_framework.exceptions import ValidationError

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from . import serializers
from postmaker.models import Release
from postmaker.postautomation import new_release_entry

class CreateWithReturnDataMixin:
    # basic mixin handles api create action with return data
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            return_data = self.perform_create(serializer)
            return Response(return_data, status=status.HTTP_200_OK)
        except Exception as err:
            raise ValidationError({'error': err})
    
    def perform_create(self, serializer):
        return serializer.save()

class CreateWithNoModelAPIView(GenericAPIView):
    # basic view with no query set
    # cannot retrieve data (no list/retrieve view)
    allowed_methods = ['POST', 'OPTIONS']
    def get_queryset(self):
        return None

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class CreateWithReturnDataGenericAPIView(CreateWithReturnDataMixin, CreateWithNoModelAPIView):
    pass


class ReleaseAPIViewSet(ModelViewSet):
    """
    Full set of views to accomplish CURD to 'release' data model
    """
    queryset = Release.objects.all()
    serializer_class = serializers.ReleaseSerializer

    def perform_create(self, serializer):
        obj = serializer.save()
        # hook in autopost
        if self.request.GET.get('do_not_post'): return
        new_release_entry(obj)

class NpAccountLoginAPIView(CreateWithReturnDataGenericAPIView):
    """
    Log in to Np using the provided credential. Returns a cdb_auth cookie.
    """
    serializer_class = serializers.NpAccountSerializer

class NpPostActionAPIView(CreateWithReturnDataGenericAPIView):
    """
    Create/edit post with provided data. Returns an object containing the url of the specified post 
    """
    def get_serializer_class(self):
        if self.kwargs['action'] == 'new':
            return serializers.NpCreateThreadSerializer
        if self.kwargs['action'] == 'edit':
            return serializers.NpEditThreadSerializer

class NpPostReleaseWithaIDAPIView(CreateWithReturnDataGenericAPIView):
    """
    Auto post specified release to forum with supplied Adam ID 
    """
    serializer_class = serializers.ReleaseWithaIDSerializer

class NpSetReleaseAsPostedAPIView(CreateWithReturnDataGenericAPIView):
    """
    Set specified release to posted and save post url 
    """
    serializer_class = serializers.ReleaseWithForumPostURLSerializer

class BaalCreateShareLinkAPIView(CreateWithReturnDataGenericAPIView):
    """
    Generate a share link for the specified file
    """
    serializer_class = serializers.BaalShareLinkCreateSerializer

class AplMusicFetchContentAPIView(CreateWithReturnDataGenericAPIView):
    """
    API view for parsing Apple Music collection view
    """
    serializer_class = serializers.AplMusicSerializer