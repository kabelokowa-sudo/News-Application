from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class RegisterForm(UserCreationForm):
    """
    Front-end sign-up form. Lets a new user pick their role
    (Reader, Editor, or Journalist) at registration time.

    Saving the resulting CustomUser triggers the `sync_user_role`
    signal (see signals.py), which automatically puts the user in
    the matching Group and grants the permissions that go with it -
    no extra group-assignment code is needed here.
    """

    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=CustomUser.Role.choices, required=True)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user
