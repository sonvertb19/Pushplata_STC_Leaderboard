from django.urls import path
from main import views as main_views

urlpatterns = [
    path("", main_views.home_view, name="home"),
    path("quiz_leaderboard/", main_views.quiz_leaderboard, name="quiz_leaderboard"),
    path("siteadmin/login/", main_views.site_admin_login, name="site_admin_login"),
    path("siteadmin/logout/", main_views.site_admin_logout, name="site_admin_logout"),
    path("siteadmin/upload/", main_views.upload_quiz_data, name="upload_quiz_data"),
]