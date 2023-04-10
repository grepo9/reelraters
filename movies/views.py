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
    movies = Movie.objects.filter(user=request.user)
    return render(request, 'movies/movie_list.html', {'movies': movies})

@login_required
def add_movie(request):
    if request.method == 'POST':
        if 'show_movies' in request.POST:
            title = request.POST.get('title')
            data = get_movie_info(title)
            if not data:
                return render(request, 'movies/add_movie.html', {'posters': None})
            currently_displayed_movies = data.get('Search')
            if not currently_displayed_movies:
                return render(request, 'movies/add_movie.html', {'posters': None})
            else:
                request.session['shown_movies'] = currently_displayed_movies
            posters = []
            for i in currently_displayed_movies:
                posters.append(i['Poster'])
            return render(request, 'movies/add_movie.html', {'posters': posters})
        elif any(item.startswith("movie--") for item in request.POST):
            for key, value in request.POST.items():
                if key.startswith('movie'):
                    movie_index = int(key.replace('movie--', ''))
            selected_movie = request.session.get('shown_movies')[movie_index]
            movie = Movie.objects.create(title=selected_movie['Title'], year=selected_movie['Year'], imdb_id=selected_movie['imdbID'], poster_image_url=selected_movie['Poster'], user=request.user)
            return redirect('movie_list')

    return render(request, 'movies/add_movie.html')

@login_required
def rate_movie(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    existed_rating = Rating.objects.filter(movie=movie, user=request.user).first()
    existed_review = Review.objects.filter(movie=movie, user=request.user).first()
    print('DOES IT EXIST', existed_review)
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
        return redirect('movie_list')
    return render(request, 'movies/rate_movie.html', {'movie': movie, 'existed_review': existed_review, 'existed_rating': existed_rating})

@login_required
def remove_movie(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    movie.delete()
    return redirect('movie_list')


def get_movie_info(title, year=None):
    api_key = '506845f9'
    if year:
        url = f'http://www.omdbapi.com/?apikey={api_key}&t={title}&y={year}&plot=short&r=json&type=movie'
    else:
        url = f'http://www.omdbapi.com/?apikey={api_key}&s={title}&plot=short&r=json'
    response = requests.get(url)
    data = response.json()
    return data

def get_box_office_movies():
    api_key = 'k_y27rgm8b'
    url = f'https://imdb-api.com/en/API/BoxOffice/{api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        box_office_movies = response.json()['items']
        cache.set('box_office_movies', box_office_movies, 60*60*24) # cache for 24 hours
        return box_office_movies
    else:
        # handle API error
        return

def home_page(request):
    box_office_movies = cache.get('box_office_movies')
    if not box_office_movies:
        box_office_movies = get_box_office_movies()
    return render(request, 'home_page.html', {'box_office_movies': box_office_movies})

def add_imdb_movie(request):
    # Extract movie information from the JSON object
    imdb_movie = json.loads(request.POST.get('imdb_movie').replace("'", "\""))
    title = imdb_movie.get('title')
    year = 2020
    imdb_id = imdb_movie.get('id')
    poster_image_url = imdb_movie.get('image').replace('_V1_Ratio0.6716_AL.jpg', '_V1_SY200.jpg')

    # # Create a new Movie object and save it to the database
    Movie.objects.create(title=title, year=year, imdb_id=imdb_id, poster_image_url=poster_image_url, user=request.user)

    # Redirect the user to their movie list
    return redirect('movie_list')
