import requests


def get_wb_categories() -> dict:
    """Сбор категорий wb"""

    url = 'https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v3.json'
    
    return requests.get(url).json()


def parse_page(page: int = 1, shard:str = None, query:str = None, low_price:int = None, top_price:int = None) -> dict:
    """Сбор товаров со страницы"""

    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0"}

    url = f'https://catalog.wb.ru/catalog/{shard}/v2/catalog?appType=1&curr=rub' \
          f'&dest=-1257786' \
          f'&locale=ru' \
          f'&page={page}'
    if low_price:
        url += f'&priceU={low_price * 100}'
    if top_price:
        url += f';{top_price * 100}'
    url += f'&sort=popular&spp=0'
    if query:
        url += f'&{query}'
    print(url)
    r = requests.get(url, headers=headers)

    return r.json()
