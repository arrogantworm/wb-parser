from django.contrib import admin
from .models import Category, Product, Size, SearchQuery


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'shard', 'query')
    list_filter = ('shard',)
    search_fields = ('name', 'url', 'query')
    autocomplete_fields = ('parent',)
    ordering = ('name',)


class SizeInline(admin.TabularInline):
    model = Size
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'brand_id', 'review_rating', 'feedbacks')
    list_filter = ('brand',)
    search_fields = ('name', 'wb_id', 'brand', 'brand_id')
    autocomplete_fields = ('category',)
    inlines = [SizeInline]
    ordering = ('name',)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'size_id', 'price', 'discounted_price')
    search_fields = ('product__name', 'name', 'size_id')
    autocomplete_fields = ('product',)
    ordering = ('product', 'name')


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'count', 'created', 'last_search')
    search_fields = ('query',)
    ordering = ('-last_search',)
    raw_id_fields = ('products',)
