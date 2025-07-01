from celery import shared_task
from django.core.cache import cache
from wb_parser import parser
from .models import Category, Product, Size


@shared_task
def save_category_to_database(category_id:int):

    category_path = parser.search_category_by_id(category_id)

    for category in category_path:

        parent_id = category.get('parent')

        parent_obj = None
        if parent_id:
            parent_obj = Category.objects.filter(wb_id=parent_id).first()

        Category.objects.update_or_create(
            wb_id=category['id'],
            defaults={
                'name': category['name'],
                'url': category['url'],
                'parent': parent_obj,
                'shard': category['shard'],
                'query': category['query'],
            }
        )

    # Запускаем сразу парсинг товаров
    parse_products_for_category.delay(category_id)


@shared_task
def parse_products_for_category(category_id: int, n: int = 2):
    """ Собираем данные о товарах по категории,
        n - количество страниц, максимум n=50 """

    category = Category.objects.get(wb_id=category_id)

    category_shard = category.shard
    category_query = category.query

    for page in range(1, n+1):
        products = parser.parse_page(page, category_shard, category_query)
        products = products.get('data')
        products = products.get('products')

        for product in products:

            product_obj, updated = Product.objects.update_or_create(
                wb_id=product['id'],
                defaults={
                    'category': category,
                    'name': product.get('name'),
                    'brand': product.get('brand'),
                    'brand_id': product.get('brandId'),
                    'review_rating': product.get('reviewRating'),
                    'feedbacks': product.get('feedbacks'),
                    'quantity': product.get('totalQuantity'),
                }
            )

            for size in product['sizes']:
                Size.objects.update_or_create(
                    size_id=size['optionId'],
                    defaults={
                        'product': product_obj,
                        'name': size['name'],
                        'price': size['price']['basic'] / 100,
                        'discounted_price': size['price']['product'] / 100,
                    }
                )

    cache.set(f'parsing_category_{category_id}', 'done', 3600)
