from django.shortcuts import render
from . import parser


def main_view(request):
    categories = parser.get_wb_categories()

    return render(
        request,
        'main.html',
        {'categories': categories}
    )


def categories_view(request):
    categories = parser.get_wb_categories()

    return render(
        request,
        'categories.html',
        {'categories': categories}
    )


def items_view(request):
    category = 'Белье для мальчиков'
    items = parser.parse_page(1, 'children_boys2', 'cat=8331')
    items = items.get('data')
    items = items.get('products')

    return render(
        request,
        'items.html',
        {
            'category': category,
            'items': items,
         }
    )
