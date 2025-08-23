import datetime
import re


def format_time(time):
    '''Функция для очистки строки от не нужных символов'''
    ftime = re.search(r'(\d{2}):(\d{2})', time)
    print(ftime.group(1))
    return ftime.group(1)

def check_time(date):
    '''Функция для проверки совпадения времени новости и настоящего времени. Надо разделить на 2 функции'''
    date = format_time(date)
    news_time = datetime.datetime.strptime(date, '%H').time()
    news_time = news_time.strftime('%H')
    print(news_time)#Где нибудь здесь разделение
    date1 = datetime.datetime.now().strftime('%H')
    date2 = datetime.time(22, 0, 0).strftime('%H')
    date3 = news_time == date1
    print(date3)

check_time('22:06')