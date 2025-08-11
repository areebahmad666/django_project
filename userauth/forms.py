from django import forms
from userauth.models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model=UserProfile
        fields=('picture')