from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

class Blogger(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    created_date = models.DateTimeField(default=timezone.now)

    def get_absolute_url(self):
        return reverse('blogger-detail', args=[str(self.id)])

    def __str__(self):
        return self.user.username

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Blogger, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(auto_now=True)
    is_protected = models.BooleanField(default=False)
    password = models.CharField(max_length=50, blank=True)
    audio_file = models.FileField(upload_to='blog_audio/', blank=True, null=True)
    has_audio = models.BooleanField(default=False)
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    image_caption = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-created_date']

    def get_absolute_url(self):
        return reverse('blog-detail', args=[str(self.id)])

    def __str__(self):
        return self.title[:75]

    def check_password(self, password):
        return self.password == password

    def get_likes_count(self):
        return self.likes.count()

    def is_liked_by(self, user):
        return self.likes.filter(user=user).exists()

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='likes')
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'post']

    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"

class Comment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f'{self.content[:75]}...'

class SavedBlog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    saved_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'post']
        ordering = ['-saved_date']

    def __str__(self):
        return f"{self.user.username} saved {self.post.title}"
