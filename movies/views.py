from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import requests
from .models import Movie, Rating, Review
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.core.cache import cache
import json
import ast
from django.db import models


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

class MyLoginView(LoginView):
    template_name = 'login.html'

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    return render(request, 'profile.html')

@login_required
def movie_list(request):
    movies = Movie.objects.filter(user=request.user).annotate(
        most_recent_review_date=models.Max('reviews__review_date')
    ).order_by('-most_recent_review_date')

    return render(request, 'movies/movie_list.html', {'movies': movies})

@login_required
def add_movie(request):
    if request.method == 'POST':
        if 'show_movies' in request.POST:
            title = request.POST.get('title')
            year = request.POST.get('year')
            data = get_movie_info(title,  year=year)  
            if not data or 'results' not in data:
                return render(request, 'movies/add_movie.html', {'posters': None})
            currently_displayed_movies = data['results']
            if not currently_displayed_movies:
                return render(request, 'movies/add_movie.html', {'posters': None})
            else:
                request.session['shown_movies'] = currently_displayed_movies
            posters = [movie['poster_path'] for movie in currently_displayed_movies]
            return render(request, 'movies/add_movie.html', {'posters': posters})
        elif any(item.startswith("movie--") for item in request.POST):
            for key, value in request.POST.items():
                if key.startswith('movie'):
                    movie_index = int(key.replace('movie--', ''))
            selected_movie = request.session.get('shown_movies')[movie_index]
            print('SELECTED_MOVIE', selected_movie)
            imdb_id = selected_movie['id']
            existing_movie = Movie.objects.filter(user=request.user, imdb_id=imdb_id).exists()
            if not existing_movie:
                Movie.objects.create(title=selected_movie['title'], year=selected_movie['release_date'][:4], imdb_id=selected_movie['id'], poster_image_url=selected_movie['poster_path'], user=request.user)
            return redirect('movie_list')

    return render(request, 'movies/add_movie.html')


@login_required
def rate_movie(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    existed_rating = Rating.objects.filter(movie=movie, user=request.user).first()
    existed_review = Review.objects.filter(movie=movie, user=request.user).first()
    if request.method == 'POST':
        rating = request.POST.get('rating')
        review = request.POST.get('review')
        if existed_review:
            existed_review.review = review
            existed_review.save()
        else:
            Review.objects.create(movie=movie, review=review, user=request.user)
        if existed_rating:
            existed_rating.rating = rating
            existed_rating.save()
        else:
            Rating.objects.create(movie=movie, rating=rating, user=request.user)
        movie.rating_count += 1
        movie.save()
        return redirect('movie_list')
    return render(request, 'movies/rate_movie.html', {'movie': movie, 'existed_review': existed_review, 'existed_rating': existed_rating})

@login_required
def remove_movie(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    movie.delete()
    return redirect('movie_list')


def get_movie_info(title, adult=False, year=None):
    url = f"https://api.themoviedb.org/3/search/movie?query={title}"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlMTJjNzcyN2ZjZDJmOTVlNDUzNDU3ZGM3NzEwOTljZSIsInN1YiI6IjY0YzViMzc1ZWVjNWI1MDBlMjNiZDRmOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.JEiw80j42f2XkDCpm8iDhuWAnLXPMUG0ChVdejtxn5g"
    }
    if adult:
        url += "&include_adult=true"
    else:
        url += "&include_adult=false"
    
    if year:
        url += f"&year={year}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Failed to fetch data from the MovieDB API.")

def get_box_office_movies():
    url = "https://api.themoviedb.org/3/movie/now_playing"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlMTJjNzcyN2ZjZDJmOTVlNDUzNDU3ZGM3NzEwOTljZSIsInN1YiI6IjY0YzViMzc1ZWVjNWI1MDBlMjNiZDRmOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.JEiw80j42f2XkDCpm8iDhuWAnLXPMUG0ChVdejtxn5g"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        box_office_movies = response.json()['results']
        return box_office_movies
    else:
        # handle API error
        print('Failed to fetch box office movies')
        return []

def home_page(request):
    box_office_movies = cache.get('box_office_movies')
    if not box_office_movies:
        box_office_movies = get_box_office_movies()
    return render(request, 'home_page.html', {'box_office_movies': box_office_movies})

def add_imdb_movie(request):
    # Extract movie information from the JSON object
    # needs to be double quotes to load

    # imdb_movie = json.loads(request.POST.get('imdb_movie').replace("'", "\"").replace("True", "true").replace("False", "false"))
    imdb_movie = ast.literal_eval(request.POST.get('imdb_movie'))
    
   
    title = imdb_movie.get('title')
    date_string = imdb_movie.get('release_date')
    year = date_string.split("-")[0]

    imdb_id = imdb_movie.get('id')
    poster_image_url = imdb_movie.get('poster_path')

    existing_movie = Movie.objects.filter(user=request.user, imdb_id=imdb_id).exists()

    if not existing_movie:
        # Movie with the same imdb_id doesn't exist for the user, create a new Movie object
        Movie.objects.create(title=title, year=year, imdb_id=imdb_id, poster_image_url=poster_image_url, user=request.user)

    # Redirect the user to their movie list
    return redirect('movie_list')
