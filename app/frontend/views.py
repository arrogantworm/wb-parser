from django.contrib import messages
from django.shortcuts import render, redirect, reverse
from wb_parser import parser
from api.models import Category


def main_view(request):
    categories = parser.get_wb_categories()

    return render(
        request,
        'main/main.html',
        {'categories': categories}
    )


def products_view(request):

    category_id = request.GET.get('category_id')
    search_query = request.GET.get('q')

    context = {}

    # Результаты по категории
    if category_id:
        context['type'] = 'category'

    # Результаты через поиск
    elif search_query:
        context['type'] = 'search'

    else:
        messages.error(request, 'Неверный запрос')
        return redirect(reverse('frontend:main'))

    return render(
        request,
        'products/products.html',
        context=context,
    )
