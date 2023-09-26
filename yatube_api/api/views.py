from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, mixins
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from posts.models import Comment, Follow, Group, Post
from .permissions import AuthorOrReadOnly
from .serializers import (CommentSerializer, FollowPOSTSerializer,
                          FollowSerializer, GroupSerializer, PostSerializer)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (AuthorOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)


class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = (AuthorOrReadOnly,)

    def list(self, request, post_id):
        queryset = Comment.objects.filter(post=post_id)
        serializer = CommentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, post_id=post.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk, post_id):
        queryset = Comment.objects.filter(post=post_id)
        comment = get_object_or_404(queryset, pk=pk)
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk, post_id):
        comment = get_object_or_404(Comment, post_id=post_id, pk=pk)
        serializer = CommentSerializer(
            comment, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk, post_id):
        comment = get_object_or_404(Comment, post_id=post_id, pk=pk)
        serializer = CommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk, post_id):
        comment = get_object_or_404(Comment, post_id=post_id, pk=pk)
        if request.user == comment.author:
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class FlollowViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):

    def list(self, request):
        search_query = self.request.query_params.get('search', None)
        if search_query:
            following = Follow.objects.filter(
                following__username=search_query, user=request.user
            )
        else:
            following = Follow.objects.filter(user=request.user)
        serializer = FollowSerializer(following, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = FollowPOSTSerializer(data=request.data)
        following = request.data.get('following')
        if serializer.is_valid():
            if Follow.objects.filter(
                user=request.user, following__username=following
            ).exists():
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
            if request.user.username == following:
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
