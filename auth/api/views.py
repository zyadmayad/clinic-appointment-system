from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth.permissions import IsAdmin
from auth.api.serializer import UserSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_list(request):
    if request.method == 'GET':
        users = User.objects.prefetch_related('groups').all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_detail(request, user_id):
    user = get_object_or_404(User.objects.prefetch_related('groups'), pk=user_id)

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    if request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = UserSerializer(user, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_detail(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
