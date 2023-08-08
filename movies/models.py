from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Movie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    year = models.IntegerField()
    imdb_id = models.CharField(max_length=10, blank=True, null=True)
    poster_image_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    rating_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.year}) by {self.user.username}"

class Rating(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    rating = models.FloatField (choices=([(i, i) for i in range(1, 6)]))
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Rating for '{self.movie.title}' by {self.user.username}"

    class Meta:
        unique_together = (('user', 'movie'),)
        index_together = (('user', 'movie'),)

class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.TextField()
    review_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for '{self.movie.title}' by {self.user.username}"

    class Meta:
        unique_together = (('user', 'movie'),)
        index_together = (('user', 'movie'),)
