from django.db import models


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

    shard = models.CharField(max_length=255)
    query = models.CharField(max_length=255)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["shard"]),
            models.Index(fields=["query"]),
        ]


class Product(models.Model):

    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
        db_index=True,
    )

    name = models.CharField(max_length=255, db_index=True)
    wb_id = models.BigIntegerField(unique=True)

    brand = models.CharField(max_length=255, db_index=True)
    supplier_id = models.BigIntegerField(db_index=True)

    review_rating = models.PositiveIntegerField(default=0, db_index=True)
    feedbacks = models.PositiveIntegerField(default=0, db_index=True)

    quantity = models.PositiveIntegerField(default=0)

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

    name = models.CharField(max_length=255)
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
