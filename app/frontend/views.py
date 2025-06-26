from django.shortcuts import render
from wb_parser import parser


def main_view(request):
    categories = parser.get_wb_categories()

    return render(
        request,
        'main/main.html',
        {'categories': categories}
    )


def products_view(request):
    return render(
        request,
        'products/products.html'
    )
