from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django.core import serializers

from posts.models import Post

import json
import requests

postId = openapi.Parameter('postId', openapi.IN_QUERY, description="Post ID", type=openapi.TYPE_INTEGER)
userId = openapi.Parameter('userId', openapi.IN_QUERY, description="User ID", type=openapi.TYPE_INTEGER)
title = openapi.Parameter('title', openapi.IN_QUERY, description="Title", type=openapi.TYPE_STRING)
body = openapi.Parameter('body', openapi.IN_QUERY, description="Body", type=openapi.TYPE_STRING)

@swagger_auto_schema(method='get',
                     manual_parameters=[postId, userId],
                     operation_description='Retrieves user posts either by postId or by userId.',
                     responses= {
                       200: 'Post with provided postId or userId.',
                       400: 'Neither postId nor userId provided.',
                       404: 'Post not found for postId or userId.'
                    })
@swagger_auto_schema(method='put',
                     manual_parameters=[postId, userId, title, body],
                     operation_description='Creates (if postId missing) or modifies (ignores userId) user posts.',
                     responses= {
                       200: 'postId of the created/modified post.',
                       400: 'invalid userID, title or body length.',
                       404: 'Post with postId does not exist.'
                     })
@swagger_auto_schema(method='delete',
                     manual_parameters=[postId],
                     operation_description='Deleted user posts.',
                     responses= {
                       200: 'Post deleted successfully.',
                       400: 'Post does not exist.'
                     })
@api_view(['GET', 'PUT', 'DELETE'])
def post(request):
  """
  Manages retrieval, creation, modification and deletion of user posts.
  """
  if request.method == 'GET':
    return get_post(request)
  if request.method == 'PUT':
    return put_post(request)
  if request.method == 'DELETE':
    return delete_post(request)
  return Response('Invalid method', status.HTTP_400_BAD_REQUEST)

def get_post(request):
  """
  Retrieves user posts.
  """
  pId = request.GET.get('postId')
  uId = request.GET.get('userId')

  if pId:
    try:
      post = Post.objects.get(id=pId)
    except Post.DoesNotExist:
      print('Post with ', pId, 'not found')
      external_post = json.loads(requests.get(f'https://jsonplaceholder.typicode.com/posts/{pId}').text)
      if 'id' not in external_post:
        return Response(f'Post with Id={pId} not found.', status=status.HTTP_404_NOT_FOUND)
      post = Post(id=pId, userId=external_post['userId'], title=external_post['title'], body=external_post['body'])
      post.save()
    return Response(serializers.serialize('json', [post]))
  
  if uId:
    posts = Post.objects.filter(userId=uId)
    if not posts:
      external_posts = json.loads(requests.get(f'https://jsonplaceholder.typicode.com/posts/?userId={uId}').text)
      if len(external_posts) == 0:
        return Response(f'Post with userId={pId} not found.', status=status.HTTP_404_NOT_FOUND)
      posts = []
      for post in external_posts:
        p = Post(id=post['id'], userId=uId, title=post['title'], body=post['body'])
        p.save()
        posts.append(p)
    return Response(serializers.serialize('json', posts))

  return Response('Neither postId nor userId provided.', status=status.HTTP_400_BAD_REQUEST)

def put_post(request):
  """
  Creates/modifies user posts.
  """
  pId = request.GET.get('postId')
  uId = request.GET.get('userId')
  titleParam = request.GET.get('title') or ''
  bodyParam = request.GET.get('body') or ''
  
  # this is creation
  if not pId:
    if not uId or len(titleParam) > 255 or len(bodyParam) > 1024:
      return Response('userId missing, or length of body > 255 or length of title > 1024', status=status.HTTP_400_BAD_REQUEST)
    if not 'id' in json.loads(requests.get(f'https://jsonplaceholder.typicode.com/users/{uId}').text):
      return Response('Invalid userId', status=status.HTTP_400_BAD_REQUEST)
    post = Post(userId=uId, title=titleParam, body=bodyParam)
    post.save()
    return Response(post.id)
  # this is modification
  else:
    try:
      post = Post.objects.get(id=pId)
    except Post.DoesNotExist:
      return Response(f'Post with id={pId} does not exist', status=status.HTTP_400_BAD_REQUEST)
    post.title = titleParam
    post.body = bodyParam
    post.save()
    return Response(serializers.serialize('json', [post]))

def delete_post(request):
  """
  Deletes user posts.
  """
  pId = request.GET.get('postId')
  if not pId:
    return Response('Post with id={pId} does not exist', status=status.HTTP_400_BAD_REQUEST)
  try:
    post = Post.objects.get(id=pId)
  except Post.DoesNotExist:
    return Response(f'Post with id={pId} does not exist', status=status.HTTP_400_BAD_REQUEST)
  post.delete()
  return Response()
