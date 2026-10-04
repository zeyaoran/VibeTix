from django.db import models
from django.utils.text import slugify


class Artist(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    bio = models.TextField(blank=True)
    genre = models.CharField(max_length=80, blank=True)
    image = models.ImageField(upload_to='artists/', blank=True, null=True)
    instagram_handle = models.CharField(max_length=100, blank=True)
    spotify_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Artist'
        verbose_name_plural = 'Artists'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    capacity = models.PositiveIntegerField(help_text="Total venue maximum capacity")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    image = models.ImageField(upload_to='venues/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['city', 'name']
        verbose_name = 'Venue'
        verbose_name_plural = 'Venues'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.city}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.city}"


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        ON_SALE = 'ON_SALE', 'On Sale'
        SOLD_OUT = 'SOLD_OUT', 'Sold Out'
        POSTPONED = 'POSTPONED', 'Postponed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name='events')
    artists = models.ManyToManyField(Artist, related_name='events', blank=True)
    banner_image = models.ImageField(upload_to='events/banners/', blank=True, null=True)
    thumbnail_image = models.ImageField(upload_to='events/thumbnails/', blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    doors_open = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )
    age_restriction = models.CharField(max_length=50, default='All Ages')
    video_url = models.URLField(max_length=300, blank=True, null=True, help_text="YouTube or teaser video URL")
    terms_conditions = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.start_time.strftime('%Y-%m-%d')})"

    @property
    def youtube_embed_url(self):
        if not self.video_url:
            return None
        import re
        # Support formats: youtube.com/watch?v=ID, youtu.be/ID, youtube.com/embed/ID
        match = re.search(r'(?:v=|\/embed\/|youtu\.be\/|\/v\/|watch\?v=|\&v=)([^#\&\?]+)', self.video_url)
        if match:
            return f"https://www.youtube.com/embed/{match.group(1)}"
        return self.video_url
