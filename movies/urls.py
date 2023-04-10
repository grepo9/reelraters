from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.movie_list, name='movie_list'),
    path('add/', views.add_movie, name='add_movie'),
    # path('add/', views.show_relevant_movies, name='show_relevant_movies'),
    path('<int:movie_id>/rate/', views.rate_movie, name='rate_movie'),
    path('<int:movie_id>/remove/', views.remove_movie, name='remove_movie'),
    path('', views.home_page, name='home_page'),
    path('add_imdb_movie/', views.add_imdb_movie, name='add_imdb_movie'),
]
