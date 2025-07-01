from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from wb_parser import parser
from .models import Category, Product, Size
from .serializers import ProductSerializer
from . import tasks


class ProductParseView(APIView):

    def get(self, request):

        query_params = request.query_params

        # Клик на категорию
        if 'category_id' in query_params:

            category_id = query_params.get('category_id')

            if not category_id.isdigit():
                return Response({'status': 'error', 'error': 'ID категории должно быть числом'}, status=status.HTTP_400_BAD_REQUEST)

            category_id = int(category_id)

            task_id = f'parsing_category_{category_id}'
            parsing_status = cache.get(task_id)
            print(f'Task state: {parsing_status}', flush=True)

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
            # TODO: реализовать функционал поиска
            pass

        return Response(status=status.HTTP_400_BAD_REQUEST)


class ProductPagination(PageNumberPagination):
    page_size = 20


class ProductListAPIView(ListAPIView):

    serializer_class = ProductSerializer
    pagination_class = ProductPagination

    def get_queryset(self):

        category_id = self.request.query_params.get('category_id')

        # По категории
        if not category_id:
            return Product.objects.none()

        qs = Product.objects.filter(category__wb_id=category_id).prefetch_related('sizes')

        # Фильтрация
        min_price = self.request.query_params.get('min_price')
        top_price = self.request.query_params.get('top_price')
        min_rating = self.request.query_params.get('min_rating')
        min_feedbacks = self.request.query_params.get('min_feedbacks')

        if min_price:
            qs = qs.filter(sizes__price__gte=min_price)
        if top_price:
            qs = qs.filter(sizes__price__lte=top_price)
        if min_rating:
            qs = qs.filter(review_rating__gte=min_rating)
        if min_feedbacks:
            qs = qs.filter(feedbacks__gte=min_feedbacks)

        # Сортировка
        ordering = self.request.query_params.get('sort')
        if ordering in ['name', '-name', 'price', '-price', 'discounted_price', '-discounted_price', 'rating', '-rating', 'feedbacks', '-feedbacks']:
            match ordering:
                case 'name':
                    qs = qs.order_by(ordering)
                case '-name':
                    qs = qs.order_by(f'-{ordering[1:]}')
                case 'price':
                    qs = qs.order_by(f'sizes__{ordering}')
                case '-price':
                    qs = qs.order_by(f'-sizes__{ordering[1:]}')
                case 'discounted_price':
                    qs = qs.order_by(f'sizes__{ordering}')
                case '-discounted_price':
                    qs = qs.order_by(f'-sizes__{ordering[1:]}')
                case 'rating':
                    qs = qs.order_by('review_rating')
                case '-rating':
                    qs = qs.order_by('-review_rating')
                case 'feedbacks':
                    qs = qs.order_by(ordering)
                case '-feedbacks':
                    qs = qs.order_by(f'-{ordering[1:]}')

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
