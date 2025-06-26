from django.contrib import admin
from .models import Category, Product, Size


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
    list_display = ('name', 'category', 'brand', 'supplier_id', 'review_rating', 'feedbacks')
    list_filter = ('brand',)
    search_fields = ('name', 'wb_id', 'brand', 'supplier_id')
    autocomplete_fields = ('category',)
    inlines = [SizeInline]
    ordering = ('name',)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'size_id', 'price', 'discounted_price')
    search_fields = ('product__name', 'name', 'size_id')
    autocomplete_fields = ('product',)
    ordering = ('product', 'name')
