from django import template

register = template.Library()

@register.filter
def rating_stars(rating):
    if not rating:
        return '<p style="color:#E0E0E0; text-align: center"> No rating yet </p>'
    full_stars = int(rating)

    half_star = round((rating - full_stars) * 2)
    empty_stars = 5 - full_stars - half_star
    return '<p class="fas fa-star"></p>' * full_stars + '<p class="fas fa-star-half-alt"></p>' * half_star + '<i class="far fa-star"></i>' * empty_stars
