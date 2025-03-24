from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db.models import Count
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from .models import BlogPost, Comment, Blogger, Like, SavedBlog
from .forms import BlogPostForm, CommentForm, BloggerForm, ExtendedUserCreationForm, CustomPasswordResetForm
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site

class BlogListView(ListView):
    model = BlogPost
    template_name = 'blog/blogpost_list.html'
    context_object_name = 'posts'
    ordering = ['-created_date']
    paginate_by = 10

class BlogDetailView(DetailView):
    model = BlogPost
    template_name = 'blog/blogpost_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['comments'] = self.object.comment_set.all().order_by('-created_date')
        
        # Check if user has access to password-protected post
        if self.object.is_protected:
            context['has_access'] = self.request.session.get(f'post_access_{self.object.pk}', False)
        else:
            context['has_access'] = True
            
        if self.request.user.is_authenticated:
            context['user_has_liked'] = self.object.is_liked_by(self.request.user)
        return context

@login_required
def create_blog_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            blogger = Blogger.objects.get(user=request.user)
            post.author = blogger
            post.save()
            messages.success(request, 'Blog post created successfully!')
            return redirect('blog-detail', pk=post.pk)
    else:
        form = BlogPostForm()
    return render(request, 'blog/create_blog_post.html', {'form': form})

@login_required
def update_blog_post(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    
    # Check if user is the author
    if request.user != post.author.user:
        messages.error(request, 'You do not have permission to edit this post.')
        return redirect('blog-detail', pk=pk)
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            # If no new audio file is uploaded, keep the existing one
            if not request.FILES.get('audio_file') and post.audio_file:
                form.instance.audio_file = post.audio_file
                form.instance.has_audio = True
            
            form.save()
            messages.success(request, 'Blog post updated successfully!')
            return redirect('blog-detail', pk=pk)
    else:
        form = BlogPostForm(instance=post)
    
    return render(request, 'blog/update_blog_post.html', {
        'form': form,
        'blogpost': post
    })

@login_required
def delete_blog_post(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    if post.author.user != request.user:
        messages.error(request, 'You can only delete your own posts!')
        return redirect('blog-detail', pk=pk)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Blog post deleted successfully!')
        return redirect('blog-list')
    return render(request, 'blog/delete_blog_post.html', {'blogpost': post})

@login_required
def add_comment(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
        else:
            messages.error(request, 'Error adding comment. Please try again.')
    return redirect('blog-detail', pk=pk)

@login_required
def toggle_like(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        like.delete()
    
    return JsonResponse({
        'success': True,
        'likes_count': post.likes.count(),
        'is_liked': created
    })

def register(request):
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to DIY Blog.')
            return redirect('blog-list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExtendedUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

class BloggerListView(ListView):
    model = Blogger
    template_name = 'blog/blogger_list.html'
    context_object_name = 'bloggers'

    def get_queryset(self):
        return Blogger.objects.annotate(
            total_likes=Count('blogpost__likes'),
            post_count=Count('blogpost')
        ).filter(post_count__gt=0).order_by('-total_likes')

class BloggerDetailView(DetailView):
    model = Blogger
    template_name = 'blog/blogger_detail.html'
    context_object_name = 'blogger'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        blogger = self.get_object()
        posts = BlogPost.objects.filter(author=blogger).order_by('-created_date')
        context['posts'] = posts
        context['total_posts'] = posts.count()
        context['total_likes'] = Like.objects.filter(post__author=blogger).count()
        return context

def check_post_password(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    if request.method == 'POST':
        password = request.POST.get('password')
        if post.password == password:
            request.session[f'post_access_{post.pk}'] = True
            messages.success(request, 'Access granted!')
        else:
            messages.error(request, 'Incorrect password!')
    return redirect('blog-detail', pk=pk)

@login_required
def save_blog(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    saved_blog, created = SavedBlog.objects.get_or_create(user=request.user, post=post)
    
    if created:
        messages.success(request, 'Blog post saved successfully!')
    else:
        messages.info(request, 'Blog post was already saved.')
    
    return redirect('blog-detail', pk=pk)

@login_required
def unsave_blog(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    SavedBlog.objects.filter(user=request.user, post=post).delete()
    messages.success(request, 'Blog post removed from saved items.')
    return redirect('blog-detail', pk=pk)

class SavedBlogsListView(LoginRequiredMixin, ListView):
    model = SavedBlog
    template_name = 'blog/saved_blogs.html'
    context_object_name = 'saved_blogs'
    paginate_by = 10

    def get_queryset(self):
        return SavedBlog.objects.filter(user=self.request.user).select_related('post')

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        current_site = get_current_site(self.request)
        # Ensure the domain doesn't have any leading or trailing slashes
        site_domain = settings.SITE_DOMAIN.strip('/')
        context.update({
            'site_name': current_site.name,
            'site_domain': site_domain,
            'protocol': 'http',
        })
        super().send_mail(subject_template_name, email_template_name,
                         context, from_email, to_email, html_email_template_name)

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password-reset-complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'

class BloggerProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Blogger
    template_name = 'blog/blogger_profile_update.html'
    fields = ['bio']

    def get_success_url(self):
        return reverse_lazy('blogger-detail', kwargs={'pk': self.object.pk})

    def get_object(self):
        return self.request.user.blogger

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your profile has been updated successfully!')
        return response

@login_required
def update_user_profile(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_username':
            new_username = request.POST.get('username')
            if new_username and new_username != request.user.username:
                if User.objects.filter(username=new_username).exists():
                    messages.error(request, 'Username already exists.')
                else:
                    request.user.username = new_username
                    request.user.save()
                    messages.success(request, 'Username updated successfully!')
        
        elif action == 'update_password':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not request.user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Password updated successfully! Please login again.')
                return redirect('login')
    
    return render(request, 'blog/update_user_profile.html')
