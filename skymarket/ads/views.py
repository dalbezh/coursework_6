from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import pagination, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated

from ads.filters import AdFilter
from ads.models import Ad, Comment
from ads.permissions import IsOwner, IsAdmin
from ads.serializers import AdDetailSerializer, AdsSerializer, CommentSerializer


class AdPagination(pagination.PageNumberPagination):
    page_size = 4


class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdsSerializer
    pagination_class = AdPagination
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = AdFilter

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(author=user)

    def get_serializer_class(self):
        if self.action in ["retrieve", "create", "update", "partial_update", "destroy"]:
            return AdDetailSerializer
        return AdsSerializer

    def get_permissions(self):
        permission_classes = (AllowAny,)
        if self.action in ["retrieve"]:
            permission_classes = (AllowAny,)
        elif self.action in ["create", "update", "partial_update", "destroy", "me"]:
            permission_classes = (IsOwner | IsAdmin,)
        return tuple(permission() for permission in permission_classes)

    def get_queryset(self):
        if self.action == "me":
            return Ad.objects.filter(author=self.request.user).all()
        return Ad.objects.all()

    @action(detail=False, methods=["GET"])
    def me(self, request, *args, **kwargs):
        """
        api/ads/me
        Логика должна быть такой:
         как вернуть объявления пользователя который делает запрос
         (делается через queryset)
        """
        self.queryset = Ad.objects.filter(author=request.user)
        return super().list(request, *args, **kwargs)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        ad_id = self.kwargs.get("ad_pk")
        ad_instance = get_object_or_404(Ad, id=ad_id)
        user = self.request.user
        serializer.save(author=user, ad=ad_instance)

    def get_permissions(self):
        permission_classes = (IsAuthenticated,)
        if self.action in ["list", "retrieve"]:
            permission_classes = (IsAuthenticated,)
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = (IsOwner | IsAdmin,)
        return tuple(permission() for permission in permission_classes)

    def get_queryset(self):
        ad_id = self.kwargs.get("ad_pk")
        ad_instance = get_object_or_404(Ad, id=ad_id)
        return ad_instance.comments.all()