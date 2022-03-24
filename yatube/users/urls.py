from django.contrib.auth import views as v
from . import views
from django.urls import path

app_name = 'users'

urlpatterns = [
    path(
        'logout/',
        v.LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path(
        'login/',
        v.LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'signup/',
        views.SignUp.as_view(),
        name='signup'
    ),
    path(
        'pass_change/',
        v.PasswordChangeView.as_view(
            template_name='users/password_change_form.html'
        ),
        name='pass_change'
    ),
    path('password_change/done/',
         v.PasswordChangeDoneView.as_view(
             template_name='users/password_change_done.html'
         ),
         name='pass_change_done'),
    path('password_reset/',
         v.PasswordResetView.as_view(
             template_name='users/password_reset_form.html'
         ),
         name='reset_password'),
    path('password_reset/done/',
         v.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         v.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         v.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),


]
