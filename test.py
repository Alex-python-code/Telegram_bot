import datetime
import re

from bs4 import BeautifulSoup
import requests


def format_time(time):
    '''Функция для очистки строки от не нужных символов'''
    ftime = re.search(r'(\d{2}):(\d{2})', time)
    print(ftime.group(1))
    return ftime.group(1)

def check_time(date):
    '''Функция для проверки совпадения времени новости и настоящего времени. Надо разделить на 2 функции'''
    date = format_time(date)
    date1 = datetime.datetime.now().strftime('%H')
    date3 = date == date1
    print(date3)
    return date3

#check_time('18:06')

response = requests.get('https://lenta.ru/2025/08/24')
soup = BeautifulSoup(response.text, 'lxml')
temp = soup.find('ul', class_ = 'archive-page__container').find_all('li', class_ = 'archive-page__item _news')
for i in temp:
    time = i.find('time', class_ = 'card-full-news__info-item card-full-news__date')
    print(time.text)
