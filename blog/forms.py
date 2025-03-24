from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Comment, BlogPost, Blogger

class ExtendedUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    bio = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            blogger = Blogger.objects.create(
                user=user,
                bio=self.cleaned_data['bio']
            )
        return user

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'is_protected', 'password', 'audio_file', 'image', 'image_caption']
        widgets = {
            'password': forms.PasswordInput(),
            'content': forms.Textarea(attrs={'rows': 10}),
            'image_caption': forms.TextInput(attrs={'placeholder': 'Enter image caption (optional)'}),
        }

    def clean_audio_file(self):
        audio_file = self.cleaned_data.get('audio_file')
        if audio_file:
            if audio_file.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError('Audio file must be less than 10MB')
            
            if not audio_file.content_type.startswith('audio/'):
                raise ValidationError('Please upload a valid audio file')
            
            self.instance.has_audio = True
        return audio_file

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError('Image file must be less than 5MB')
            
            if not image.content_type.startswith('image/'):
                raise ValidationError('Please upload a valid image file')
        return image

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.has_audio = bool(instance.audio_file)
        if commit:
            instance.save()
        return instance

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your comment here...'}),
        }

class PasswordProtectedPostForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)

class BloggerForm(forms.ModelForm):
    class Meta:
        model = Blogger
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
