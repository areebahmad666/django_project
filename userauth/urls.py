from django.contrib import admin
from django.urls import path
from userauth import views
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.home),
    path('signup/', views.signup),
    path('login/',views.login_view),
    path('logoutt/',views.logout_view),
    path('upload', views.upload),
    path('like-post/<str:id>', views.likes,name='like-post'),
    path('#<str:id>', views.home_post),
    path('explore/',views.explore),
    path('profile/<str:username>/', views.profile, name='user_profile'),
    path('follow/<int:user_id>/', views.follow, name='follow'),
    path('delete/<str:id>', views.delete),
    path('search-results/', views.search_results, name='search_results'),
    path('lobby/', views.lobby),
    path('room/', views.room),
    path('get_token/', views.getTokken),
    path('create_member/', views.createMember),
    path('get_member/', views.getMember),
    path('delete_member/', views.deleteMember),
    path('News/', views.News)
]
