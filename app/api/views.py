import math
from decimal import Decimal
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Min, Max, Q, F
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from wb_parser import parser
from .models import Category, Product, Size, SearchQuery
from .serializers import ProductSerializer
from . import tasks


class ProductParseView(APIView):

    def get(self, request):

        query_params = request.query_params

        # Клик на категорию
        if 'category_id' in query_params:

            category_id = query_params.get('category_id')

            if not category_id or not category_id.isdigit():
                return Response({'status': 'error', 'error': 'ID категории должно быть числом'}, status=status.HTTP_400_BAD_REQUEST)

            category_id = int(category_id)

            task_id = f'parsing_category_{category_id}'
            parsing_status = cache.get(task_id)

            try:
                # Категория есть в БД
                category = Category.objects.get(wb_id=category_id)

                # Проверка наличия свежих данных о товарах по категории
                if not Product.objects.filter(
                        category__wb_id=category_id,
                        updated__gte=timezone.now() - timedelta(days=7),
                        parsed_from=Product.ParsedFrom.category,
                ).exists():

                    # Если данных нет или они старые - отправляем на парсинг
                    if parsing_status != 'parsing':
                        tasks.parse_products_for_category.delay(category_id)
                        cache.set(task_id, 'parsing', timeout=3600)
                        parsing_status = 'parsing'

            except Category.DoesNotExist:
                # Категории нет в БД
                category_path = parser.search_category_by_id(category_id)

                if not category_path:
                    return Response({'status': 'error', 'error': 'Категория не найдена'}, status=status.HTTP_400_BAD_REQUEST)

                # Запускаем сохранение категории в БД и парсинг товаров
                if parsing_status != 'parsing':
                    tasks.save_category_to_database.delay(category_id)
                    cache.set(task_id, 'parsing', timeout=3600)
                    parsing_status = 'parsing'

            if parsing_status == 'parsing':
                return Response({'status': 'parsing'}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'ok'}, status=status.HTTP_200_OK)

        # Поисковая строка
        elif 'q' in query_params:
            search_query = query_params.get('q')
            search_query = search_query.lower()

            # Ссылка на категорию в строке поиска
            if search_query.startswith('https://www.wildberries.ru/catalog'):
                category_url = search_query.split('https://www.wildberries.ru')[-1]
                category_path = parser.search_category_by_url(category_url)
                if category_path:
                    category_id = category_path[-1]['id']
                    return Response({'type': 'category', 'category_id': category_id}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': 'error', 'error': 'Категория не найдена'},
                                    status=status.HTTP_400_BAD_REQUEST)


            # Поисковый запрос
            else:
                if len(search_query) > 255:
                    return Response({'error': 'Слишком длинный запрос'}, status=status.HTTP_400_BAD_REQUEST)
                need_parsing = False
                try:
                    search_query_obj = SearchQuery.objects.get(query=search_query)
                    if search_query_obj.last_search < timezone.now() - timedelta(days=7):
                        search_query_obj.count = F('count') + 1
                        search_query_obj.save()
                        need_parsing = True
                except SearchQuery.DoesNotExist:
                    search_query_obj = SearchQuery.objects.create(query=search_query)
                    need_parsing = True

                task_id = f'parsing_search_{search_query_obj.pk}'
                parsing_status = cache.get(task_id)

                if parsing_status == 'parsing':
                    return Response({'type': 'search', 'status': 'parsing'}, status=status.HTTP_200_OK)

                if need_parsing:
                    tasks.parse_products_for_search.delay(search_query, search_query_obj.pk)
                    cache.set(task_id, 'parsing', timeout=3600)
                    return Response({'type': 'search', 'status': 'parsing'}, status=status.HTTP_200_OK)
                else:
                    return Response({'type': 'search', 'status': 'ok'}, status=status.HTTP_200_OK)


        return Response(status=status.HTTP_400_BAD_REQUEST)


class ProductPagination(PageNumberPagination):
    page_size = 20


class ProductListView(ListAPIView):

    serializer_class = ProductSerializer
    pagination_class = ProductPagination

    def get_queryset(self):

        category_id = self.request.query_params.get('category_id')
        search_query = self.request.query_params.get('q')

        # По категории
        if category_id:
            qs = Product.objects.filter(category__wb_id=category_id).prefetch_related('sizes')
        elif search_query:
            search_query = search_query.lower()
            try:
                search_query_obj = SearchQuery.objects.get(query=search_query)
                qs = search_query_obj.products.prefetch_related('sizes')
            except SearchQuery.DoesNotExist:
                return Product.objects.none()
        else:
            return Product.objects.none()

        # Фильтрация
        filters = Q()
        min_price = self.request.query_params.get('min_price')
        top_price = self.request.query_params.get('top_price')
        min_rating = self.request.query_params.get('min_rating')
        min_feedbacks = self.request.query_params.get('min_feedbacks')

        if min_price and min_price.isdigit():
            filters &= Q(sizes__discounted_price__gte=Decimal(min_price))
        if top_price and top_price.isdigit():
            filters &= Q(sizes__discounted_price__lte=Decimal(top_price))
        if min_rating:
            filters &= Q(review_rating__gte=min_rating)
        if min_feedbacks:
            filters &= Q(feedbacks__gte=min_feedbacks)

        qs = qs.filter(filters)

        qs = qs.annotate(
            min_discounted=Min('sizes__discounted_price'),
            min_price=Min('sizes__price')
        )

        # Сортировка
        ordering = self.request.query_params.get('sort')
        if ordering in ['name', '-name', 'price', '-price', 'discounted_price', '-discounted_price', 'rating',
                        '-rating', 'feedbacks', '-feedbacks']:
            match ordering:
                case 'name':
                    qs = qs.order_by('name')
                case '-name':
                    qs = qs.order_by('-name')
                case 'price':
                    qs = qs.order_by('min_price')
                case '-price':
                    qs = qs.order_by('-min_price')
                case 'discounted_price':
                    qs = qs.order_by('min_discounted')
                case '-discounted_price':
                    qs = qs.order_by('-min_discounted')
                case 'rating':
                    qs = qs.order_by('review_rating')
                case '-rating':
                    qs = qs.order_by('-review_rating')
                case 'feedbacks':
                    qs = qs.order_by('feedbacks')
                case '-feedbacks':
                    qs = qs.order_by('-feedbacks')

        return qs.distinct()


class CategoriesPathView(APIView):

    def get(self, request):

        query_params = request.query_params

        category_id = query_params.get('category_id')

        if not category_id.isdigit():
            return Response({'status': 'error', 'error': 'ID категории должно быть числом'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Категория есть в БД
            category = Category.objects.get(wb_id=category_id)

            category_path = category.get_path()

            return Response({'status': 'ok', 'category_path': category_path}, status=status.HTTP_200_OK)

        except Category.DoesNotExist:
            # Категории нет в БД
            task_id = f'parsing_category_{category_id}'
            parsing_status = cache.get(task_id)
            if parsing_status == 'parsing':
                return Response({'status': 'parsing'}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'error', 'error': 'Сначала нужно запустить парсинг категории'}, status=status.HTTP_404_NOT_FOUND)


class ChartDataView(APIView):

    def get(self, request):

        category_id = request.query_params.get('category_id')
        search_query = request.query_params.get('q')

        if category_id:
            if not category_id.isdigit():
                return Response({'status': 'error', 'error': 'ID категории должно быть числом'},
                                status=status.HTTP_400_BAD_REQUEST)

            category_id = int(category_id)
            products = Product.objects.filter(category__wb_id=category_id)

        elif search_query:
            search_query = search_query.lower()
            search_query_obj = get_object_or_404(SearchQuery, query=search_query)
            products = search_query_obj.products.all()

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        qs = Size.objects.filter(product__in=products)

        # фильтры цен
        min_f = request.query_params.get('min_price')
        max_f = request.query_params.get('top_price')
        min_rating = request.query_params.get('min_rating')
        min_feedbacks = request.query_params.get('min_feedbacks')
        if min_f:
            min_f = Decimal(min_f)
            qs = qs.filter(discounted_price__gte=min_f)
        if max_f:
            max_f = Decimal(max_f)
            qs = qs.filter(discounted_price__lte=max_f)
        if min_rating:
            qs = qs.filter(product__review_rating__gte=min_rating)
        if min_feedbacks:
            qs = qs.filter(product__feedbacks__gte=min_feedbacks)

        # диапазон цен
        price_range = qs.aggregate(min_price=Min('discounted_price'), max_price=Max('discounted_price'))
        min_price = price_range['min_price']
        max_price = price_range['max_price']

        if not (min_price or max_price):
            return Response({
                "price_histogram": [],
                "discount_vs_rating": []
            })

        # округляем min, max вверх до кратных 500
        min_bucket = math.floor(min_price / 500) * 500
        max_bucket = math.ceil(max_price / 500) * 500

        # шаг диапазона - примерно 6 частей диапазона, но не меньше 500
        bucket_size = max(500, math.ceil((max_bucket - min_bucket) / 6 / 500) * 500)

        # строим диапазон
        buckets = []
        current = min_bucket
        while current < max_bucket:
            buckets.append((current, current + bucket_size))
            current += bucket_size

        # собираем количество товаров
        histogram_data = []
        for low, high in buckets:
            count = qs.filter(discounted_price__gte=low, discounted_price__lt=high).count()
            histogram_data.append({
                "range": f"{low}-{high}",
                "count": count
            })

        # discount vs rating

        if min_f:
            products = products.filter(sizes__discounted_price__gte=min_f)
        if max_f:
            products = products.filter(sizes__discounted_price__lte=max_f)
        if min_rating:
            products = products.filter(review_rating__gte=min_rating)
        if min_feedbacks:
            products = products.filter(feedbacks__gte=min_feedbacks)
        products = products.prefetch_related('sizes')
        discount_vs_rating = []
        seen_pairs = set()

        for product in products:
            if product.sizes.exists():
                size = product.sizes.first()
                if size.price and size.discounted_price and size.price > 0:
                    discount_percent = int(100 - (size.discounted_price / size.price * 100))
                    rating = product.review_rating or 0

                    pair = (rating, discount_percent)
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        discount_vs_rating.append({
                            "rating": rating,
                            "discount_percent": discount_percent
                        })

        return Response({
            "price_histogram": histogram_data,
            "discount_vs_rating": discount_vs_rating
        })
