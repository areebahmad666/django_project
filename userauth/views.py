from cProfile import Profile
from itertools import chain
from urllib import request
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import Followers, Post,Profile, LikePost, RoomMember
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
import datetime
import time
import random
import requests
from agora_token_builder import RtcTokenBuilder
from .models import RoomMember
import json
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

def signup(request):
    try:
        if request.method=='POST':
            fnm=request.POST.get('fnm')
            emailid=request.POST.get('emailid')
            password=request.POST.get('password')
            print(fnm,emailid,password)
            my_user=User.objects.create_user(fnm,emailid,password)
            my_user.save()
            user_model=User.objects.get(username=fnm)
            new_profile=Profile.objects.create(user=user_model,id_user=user_model.id)
            new_profile.save()
            if my_user is not None:
                login(request,my_user)
                return redirect('/')
            return redirect('/login')
    except:
        invalid="User already exists"
        return render(request,'signup.html',{'invalid':invalid})
    return render(request,'signup.html')

def login_view(request):
    if request.method=='POST':
        fnm=request.POST.get('fnm')
        password=request.POST.get('password')
        print(fnm,password)
        user=authenticate(request,username=fnm,password=password)
        if user is not None:
            login(request,user)
            return redirect('/')
        invalid="Invalid Credentials"
        return render(request, 'login.html',{'invalid':invalid})
    return render(request,'login.html')

@login_required(login_url='/login')
def logout_view(request):
    logout(request)
    return redirect('/login')

@login_required(login_url='/login')
def home(request):
    following_users = Followers.objects.filter(follower=request.user.username).values_list('user', flat=True)
    post = Post.objects.filter(Q(user=request.user.username) | Q(user__in=following_users)).order_by('-create_at')
    profile=Profile.objects.filter(user=request.user).first()
    if not profile:
        profile=Profile.objects.create(user=request.user)
    context={
        'post':post,
        'profile': profile
    }
    return render(request, 'main.html', context)

@login_required(login_url='/login')
def upload(request):
    if request.method=='POST':
        user=request.user.username
        image=request.FILES.get('image_upload')
        caption=request.POST['caption']

        new_post=Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

        return redirect('/')
    else:
        return redirect('/')

@login_required(login_url='/login')
def likes(request, id):
    if request.method=='GET':
        username=request.user.username
        post=get_object_or_404(Post, id=id)
        like_filter=LikePost.objects.filter(post_id=id, username=username).first()
        if like_filter is None:
            new_like=LikePost.objects.create(post_id=id, username=username)
            post.no_of_likes=post.no_of_likes +1
        else:
            like_filter.delete()
            post.no_of_likes=post.no_of_likes -1
        post.save()

        print(post.id)
        return redirect('/#' + id)

@login_required(login_url='/login')
def explore(request):
    post=Post.objects.all().order_by('-create_at')
    profile=Profile.objects.get(user=request.user)

    context={
        'post':post,
        'profile':profile
    }
    return render(request, 'explore.html', context)

@login_required(login_url='/login')
def profile(request, id_user):
    # The user whose profile is being viewed
    user_object = get_object_or_404(User, username=id_user)
    user_profile = get_object_or_404(Profile, user=user_object)

    # Your own profile (for edit form)
    my_profile = Profile.objects.get(user=request.user)

    # That user's posts
    user_post = Post.objects.filter(user=user_object).order_by('-create_at')
    user_post_length = user_post.count()

    follower = request.user.username
    user = id_user

    # Follow/unfollow check
    if Followers.objects.filter(follower=follower, user=user).exists():
        follow_unfollow = 'Unfollow'
    else:
        follow_unfollow = 'Follow'

    # Follower / Following counts for that user
    user_follower = Followers.objects.filter(user=id_user).count()
    user_following = Followers.objects.filter(follower=id_user).count()

    context = {
        'user_object': user_object,
        'user_profile': user_profile,  # profile being viewed
        'user_post': user_post,
        'user_post_length': user_post_length,
        'profile': my_profile,  # your own profile
        'follow_unfollow': follow_unfollow,
        'user_follower': user_follower,
        'user_following': user_following
    }

    # Editing profile (only if it's your own)
    if request.user.username == id_user:
        if request.method == 'POST':
            bio = request.POST.get('bio')
            location = request.POST.get('location')
            image = request.FILES.get('image')

            if image:
                my_profile.profileimg = image
            my_profile.bio = bio
            my_profile.location = location
            my_profile.save()

            return redirect('/profile/' + id_user)

    return render(request, 'profile.html', context)

@login_required(login_url='/login')
def delete(request, id):
    post=Post.objects.get(id=id)
    post.delete()

    return redirect('/profile/' + request.user.username)

@login_required(login_url='/login')
def search_results(request):
    query=request.GET.get('q')
    users=Profile.objects.filter(user__username__icontains=query)
    posts=Post.objects.filter(caption__icontains=query)

    context={
        'query':query,
        'users':users,
        'posts':posts,
    }
    return render(request, 'search_user.html', context)

def home_post(request,id):
    post=Post.objects.get(id=id)
    profile=Profile.objects.get(user=request.user)
    context={
        'post':post,
        'profile':profile
    }
    return render(request, 'main.html', context)


@login_required
def follow(request, user_id):
    # user_id = the person you want to follow/unfollow
    target_user = get_object_or_404(User, id=user_id)

    # Prevent self-following
    if target_user == request.user:
        return redirect('/profile/' + target_user.username)

    # Check if already following
    existing = Followers.objects.filter(user=target_user, follower=request.user).first()

    if existing:
        existing.delete()
    else:
        Followers.objects.create(user=target_user, follower=request.user)

    return redirect('/profile/' + target_user.username)
   
def lobby(request):
    return render(request, 'lobby.html')

def room(request):
    return render(request, 'room.html')

def getTokken(request):
    appId = "d3e5547cf4834ea3bae8c6eb22b90add"
    appCertificate = "168ae34f3ba144d0ae5589e3577db718"
    channelName=request.GET.get('channel')
    uid=random.randint(1,230)
    expirationTimeInSeconds = 3600
    currentTimeStamp = int(time.time())
    privilegeExpiredTs = currentTimeStamp + expirationTimeInSeconds
    role = 1

    token = RtcTokenBuilder.buildTokenWithUid(appId, appCertificate, channelName, uid, role, privilegeExpiredTs)

    return JsonResponse({'token': token, 'uid': uid}, safe=False)

@csrf_exempt
def createMember(request):
    data = json.loads(request.body)
    member, created = RoomMember.objects.get_or_create(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )

    return JsonResponse({'name':data['name']}, safe=False)


def getMember(request):
    uid = request.GET.get('UID')
    room_name = request.GET.get('room_name')

    member = RoomMember.objects.get(
        uid=uid,
        room_name=room_name,
    )
    name = member.name
    return JsonResponse({'name':member.name}, safe=False)

@csrf_exempt
def deleteMember(request):
    data = json.loads(request.body)
    member = RoomMember.objects.get(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )
    member.delete()
    return JsonResponse('Member deleted', safe=False)

def News(request):
  url='https://newsapi.org/v2/everything?q=tesla&from=2025-07-11&sortBy=publishedAt&apiKey=b3f8d0d8aafd49709ac4edcf555d510f'
  cricket_news = requests.get(url).json()

  a = cricket_news['articles']
  desc = []
  title = []
  img = []

  for i in range(len(a)):
    f = a[i]
    title.append(f['title'])
    desc.append(f['description'])
    img.append(f['urlToImage'])

  mylist = zip(title,desc,img)
  context = {'mylist':mylist}

  return render(request, 'News.html', context)

def profile(request, username):
    # The user whose profile is being viewed
    user_object = get_object_or_404(User, username=username)
    user_profile = get_object_or_404(Profile, user=user_object)

    # Your own profile (for editing)
    my_profile = get_object_or_404(Profile, user=request.user)

    # That user's posts
    user_post = Post.objects.filter(user=user_object).order_by('-create_at')
    user_post_length = user_post.count()

    # Follow/unfollow check
    follower = request.user.username
    if Followers.objects.filter(follower=follower, user=username).exists():
        follow_unfollow = 'Unfollow'
    else:
        follow_unfollow = 'Follow'

    # Follower / Following counts for that user
    user_follower = Followers.objects.filter(user=username).count()
    user_following = Followers.objects.filter(follower=username).count()

    context = {
        'user_object': user_object,
        'user_profile': user_profile,   # profile being viewed
        'user_post': user_post,
        'user_post_length': user_post_length,
        'profile': my_profile,           # your own profile
        'follow_unfollow': follow_unfollow,
        'user_follower': user_follower,
        'user_following': user_following
    }

    # Editing profile (only if it's your own)
    if request.user.username == username:
        if request.method == 'POST':
            bio = request.POST.get('bio')
            location = request.POST.get('location')
            image = request.FILES.get('image')

            if image:
                my_profile.profileimg = image
            my_profile.bio = bio
            my_profile.location = location
            my_profile.save()

            return redirect('/profile/' + username)

    return render(request, 'profile.html', context)
