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
from django.contrib import messages
from config import MOVIEDB_API_KEY
from django.http import JsonResponse
from django.template.loader import render_to_string


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "signup.html"


class MyLoginView(LoginView):
    template_name = "login.html"


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    return render(request, "profile.html")


@login_required
def movie_list(request):
    movies = (
        Movie.objects.filter(user=request.user)
        .annotate(most_recent_review_date=models.Max("reviews__review_date"))
        .order_by("-most_recent_review_date")
    )
    if request.method == "POST":
        movie = Movie.objects.get(
            imdb_id=request.POST.get("movie_imdb_id"), user=request.user
        )
        existing_rating = Rating.objects.filter(movie=movie, user=request.user).first()
        existing_review = Review.objects.filter(movie=movie, user=request.user).first()

        return render(
            request,
            "movies/movie_list.html",
            {
                "movies": movies,
                "show_rating_modal": True,
                "selected_movie": movie,
                "existed_rating": existing_rating,
                "existed_review": existing_review,
            },
        )

    return render(request, "movies/movie_list.html", {"movies": movies})


@login_required
def add_movie(request):
    current_year = 2023

    years = range(current_year, -1, -1)
    if request.method == "POST":
        if "show_movies" in request.POST:
            title = request.POST.get("title")
            year = request.POST.get("year")
            data = get_movie_info(title, year=year)
            if not data or "results" not in data:
                return render(
                    request, "movies/add_movie.html", {"posters": None, "years": years}
                )
            currently_displayed_movies = data["results"]
            if not currently_displayed_movies:
                return render(
                    request, "movies/add_movie.html", {"posters": None, "years": years}
                )
            else:
                request.session["shown_movies"] = currently_displayed_movies
            posters = [movie["poster_path"] for movie in currently_displayed_movies]
            return render(
                request, "movies/add_movie.html", {"posters": posters, "years": years}
            )
        elif any(item.startswith("movie--") for item in request.POST):
            for key, value in request.POST.items():
                if key.startswith("movie"):
                    movie_index = int(key.replace("movie--", ""))
            selected_movie = request.session.get("shown_movies")[movie_index]
            imdb_id = selected_movie["id"]
            existing_movie = Movie.objects.filter(
                user=request.user, imdb_id=imdb_id
            ).exists()
            if not existing_movie:
                created_movie = Movie.objects.create(
                    title=selected_movie["title"],
                    year=selected_movie["release_date"][:4],
                    imdb_id=selected_movie["id"],
                    poster_image_url=selected_movie["poster_path"],
                    user=request.user,
                    description=selected_movie["overview"],
                )
                messages.success(request, "Movie added successfully.")
                return render(
                    request,
                    "movies/add_movie.html",
                    {"show_rating_modal": True, "selected_movie": created_movie},
                )
                modal_content = render_to_string("movies/rate_movie.html", {"selected_movie": created_movie})

                movie_data = {
                    "title": created_movie.title,
                    "year": created_movie.year,
                    "imdb_id": created_movie.imdb_id,
                    "poster_image_url": created_movie.poster_image_url,
                    "description": created_movie.description,
                    "modal_content": modal_content,

                }
                return JsonResponse({"show_rating_modal": True, "selected_movie": movie_data})

            else:
                messages.warning(request, "Movie already exists in your list.")
                return redirect("add_movie")
            return redirect("movie_list")

    return render(request, "movies/add_movie.html", {"years": years})


@login_required
def rate_movie(request, movie_id):
    movie = Movie.objects.get(imdb_id=movie_id, user=request.user)
    existed_rating = Rating.objects.filter(movie=movie, user=request.user).first()
    existed_review = Review.objects.filter(movie=movie, user=request.user).first()
    if request.method == "POST":
        rating = request.POST.get("rating")
        review = request.POST.get("review")
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
        return redirect("movie_list")
    return render(
        request,
        "movies/rate_movie.html",
        {
            "movie": movie,
            "existed_review": existed_review,
            "existed_rating": existed_rating,
        },
    )


@login_required
def remove_movie(request, movie_id):
    movie = Movie.objects.get(imdb_id=movie_id, user=request.user)
    movie.delete()
    messages.success(request, "Movie removed successfully")

    return redirect("movie_list")


def fetch_movies(endpoint, params=None):
    base_url = "https://api.themoviedb.org/3"
    url = f"{base_url}/{endpoint}"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {MOVIEDB_API_KEY}",
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        movies_data = response.json()
        return movies_data
    else:
        print(f"Failed to fetch movies from {endpoint}")
        return []


def get_movie_info(title, adult=False, year=None):
    params = {"query": title, "include_adult": adult, "year": year}
    return fetch_movies("search/movie", params=params)


def get_box_office_movies():
    return fetch_movies("movie/now_playing").get("results", [])


def get_popular_movies():
    params = {"language": "en-US", "page": 1}
    return fetch_movies("movie/popular", params=params).get("results", [])


def get_top_rated_movies():
    params = {"language": "en-US", "page": 1}
    return fetch_movies("movie/top_rated", params=params).get("results", [])


def home_page(request):
    box_office_movies = cache.get("box_office_movies")
    popular_movies = cache.get("popular_movies")
    top_rated_movies = cache.get("top_rated_movies")
    if not popular_movies:
        popular_movies = get_popular_movies()
        cache.set("popular_movies", popular_movies, 3600)

    if not box_office_movies:
        box_office_movies = get_box_office_movies()
        cache.set("box_office_movies", box_office_movies, 3600)

    if not top_rated_movies:
        top_rated_movies = get_top_rated_movies()
        cache.set("top_rated_movies", top_rated_movies, 3600)
    return render(
        request,
        "home_page.html",
        {
            "box_office_movies": box_office_movies,
            "popular_movies": popular_movies,
            "top_rated_movies": top_rated_movies,
        },
    )


def add_imdb_movie(request):
    # Extract movie information from the JSON object
    # needs to be double quotes to load
    imdb_movie = ast.literal_eval(request.POST.get("imdb_movie"))

    title = imdb_movie.get("title")
    date_string = imdb_movie.get("release_date")
    year = date_string.split("-")[0]

    imdb_id = imdb_movie.get("id")
    poster_image_url = imdb_movie.get("poster_path")

    existing_movie = Movie.objects.filter(user=request.user, imdb_id=imdb_id).exists()

    if existing_movie:
        messages.warning(request, "Movie already exists in your list.")
    else:
        movie = Movie.objects.create(
            title=title,
            year=year,
            imdb_id=imdb_id,
            poster_image_url=poster_image_url,
            user=request.user,
            description=imdb_movie.get("overview"),
        )
        existing_rating = Rating.objects.filter(movie=movie, user=request.user).first()
        existing_review = Review.objects.filter(movie=movie, user=request.user).first()
        messages.success(request, "Movie added successfully.")
        return render(
            request,
            "home_page.html",
            {
                "box_office_movies": get_box_office_movies(),
                "popular_movies": get_popular_movies(),
                "top_rated_movies": get_top_rated_movies(),
                "show_rating_modal": True,
                "selected_movie": movie,
                "existing_rating": existing_rating,
                "existing_review": existing_review,
            },
        )
    return redirect("home_page")
