from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):

    name = models.CharField(max_length=255, db_index=True)
    url = models.CharField(max_length=255, unique=True)

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE,
        db_index=True,
    )

    wb_id = models.BigIntegerField(unique=True)
    shard = models.CharField(max_length=255)
    query = models.CharField(max_length=2048)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'

        indexes = [
            models.Index(fields=["shard"]),
            models.Index(fields=["query"]),
        ]

    def get_path(self):
        path = []
        current = self
        while current:
            path.append((current.wb_id, current.name))
            current = current.parent
        return list(reversed(path))


class Product(models.Model):

    class ParsedFrom(models.TextChoices):
        category = 'C', 'CAT'
        search = 'S', 'SRC'

    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
        db_index=True,
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=255, db_index=True)
    wb_id = models.BigIntegerField(unique=True)

    brand = models.CharField(max_length=255, db_index=True)
    brand_id = models.BigIntegerField(db_index=True)

    review_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0,
        db_index=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    feedbacks = models.PositiveIntegerField(default=0, db_index=True)

    quantity = models.PositiveIntegerField(default=0)

    parsed_from = models.CharField(
        max_length=1,
        choices=ParsedFrom.choices,
        default=ParsedFrom.category,
        db_index=True
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

        indexes = [
            models.Index(fields=["review_rating"]),
            models.Index(fields=["feedbacks"]),
            models.Index(fields=["brand"]),
            models.Index(fields=["review_rating", "feedbacks"]),
        ]


class Size(models.Model):

    product = models.ForeignKey(
        Product,
        related_name='sizes',
        on_delete=models.CASCADE,
        db_index=True,
    )

    name = models.CharField(max_length=255, blank=True, null=True)
    size_id = models.BigIntegerField(db_index=True)

    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_index=True)
    discounted_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_index=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["price"]),
            models.Index(fields=["discounted_price"]),
            models.Index(fields=["price", "discounted_price"]),
        ]


class SearchQuery(models.Model):

    query = models.CharField(max_length=2048, db_index=True)
    products = models.ManyToManyField(Product, related_name='search_queries', blank=True, null=True)
    count = models.PositiveIntegerField(default=1)

    created = models.DateTimeField(auto_now_add=True)
    last_search = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'SearchQueries'
        ordering = ['-last_search']
