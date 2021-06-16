from rest_framework.exceptions import ValidationError

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .serializers import (
    ReleaseSerializer,
    NpAccountSerializer,
    NpCreateThreadSerializer,
    NpEditThreadSerializer
)
from postmaker.models import Release
from postmaker.postautomation import new_release_entry

class ReleaseAPIViewSet(ModelViewSet):
    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer

    def perform_create(self, serializer):
        obj = serializer.save()
        # hook in autopost
        if self.request.GET.get('do_not_post'): return
        new_release_entry(obj)
        

class NpAccountLoginAPIView(APIView):
    """
    Log in to Np using the provided credential. Returns a cdb_auth cookie.
    """
    allowed_methods = ['POST', 'OPTIONS']

    def create(self, request, *args, **kwargs):
        serializer = NpAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        np_user = serializer.login()
        if np_user:
            return Response(np_user, status=status.HTTP_200_OK)

        raise ValidationError('Invalid login credentials')

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class NpPostActionAPIView(APIView):
    """
    Manipulate post with provided data. Returns an object containing the url of the specified post 
    """
    allowed_methods = ['POST', 'OPTIONS']

    def create(self, request, *args, **kwargs):
        if self.kwargs['action'] == 'new':
            serializer = NpCreateThreadSerializer(data=request.data)
        if self.kwargs['action'] == 'edit':
            serializer = NpEditThreadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            return Response(serializer.post_thread(), status=status.HTTP_200_OK)
        except Exception as err:
            raise ValidationError(err)


    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)