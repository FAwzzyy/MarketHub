from django import forms
from django.contrib.auth.models import User


class RegisterForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self):
        user = super().save(commit=False)
        user.set_password(user.password)
        user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)