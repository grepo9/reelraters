from django import template

register = template.Library()

@register.filter
def rating_stars(rating):
    if not rating:
        return '<p style="color:#E0E0E0; text-align: center"> No rating yet </p>'

    full_stars = int(rating)
    half_star = round((rating - full_stars) * 2)
    empty_stars = 5 - full_stars - half_star

    stars_html = '<i class="fas fa-star"></i>' * full_stars
    if half_star:
        stars_html += '<i class="fas fa-star-half-alt"></i>'
    stars_html += '<i class="far fa-star"></i>' * empty_stars

    return stars_html
