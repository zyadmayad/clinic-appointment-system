from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from auth.models import Users
from auth.api.serialazer import UsersSerializer

@api_view(['GET', 'POST'])
def user_list(request):
    if request.method == 'GET':
        users = Users.objects.all()
        serializer = UsersSerializer(users, many=True)
        return Response(serializer.data)

    serializer = UsersSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def user_detail(request, user_id):
    user = get_object_or_404(Users, pk=user_id)

    if request.method == 'GET':
        serializer = UsersSerializer(user)
        return Response(serializer.data)

    if request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = UsersSerializer(user, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
