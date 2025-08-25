from bs4 import BeautifulSoup
import requests

from pathlib import Path
import datetime
import re


class TimeUtils:
    @staticmethod
    def format_time(time):
        '''Функция для очистки строки от не нужных символов'''
        ftime = re.search(r'(\d{2}):(\d{2})', time)
        #print(ftime.group(1))
        return ftime.group(1)

    
    @staticmethod
    def check_time(news_block, html_time_element, html_time_class) -> bool:
        '''Функция для проверки совпадения времени новости и настоящего времени. Надо разделить на 2 функции'''
        news_time = TimeUtils.get_news_time(news_block, html_time_element, html_time_class)
        formatted_news_time = TimeUtils.format_time(news_time)
        now_time = int(datetime.datetime.now().strftime('%H')) - 20
        conclusion = int(formatted_news_time) == now_time
        print(f'formatted_news_time: {formatted_news_time}')
        print(f'now_time: {now_time}')
        print(conclusion)
        return conclusion

    @staticmethod
    def get_news_time(news_block, time_element, time_class):
        time = news_block.find(time_element, class_ = time_class)
        print(time.text)
        return time.text


class Parser():
    """
    Класс для парсинга новостных статей с веб-сайтов.

    Атрибуты:
        1: URL главной страницы для парсинга.
        2: HTML-тег родительского элемента, содержащего новости.
        3: Класс родительского элемента, содержащего новости.
        4: HTML-тег элемента отдельной новости.
        5: Класс элемента отдельной новости.
        6: HTML-тег ссылки на подстраницу новости.
        7: Класс ссылки на подстраницу новости.
        8: HTML-тег ссылки на следующую страницу.
        9: Класс ссылки на следующую страницу.
        10: Класс блока с содержимым новости.
        11: Главный сайт, необходимый для формирования абсолютных ссылок.
    """ 
    def __init__(self, url, parent_html_news_element, parent_html_news_class,
                 html_news_element, html_news_class, sublink_element, sublink_class,
                 next_page_link_element, next_page_link_class, class_of_news_blocks, main_site,
                 time_html_class, time_html_element):
        """
        Атрибуты:
            url (str): URL главной страницы для парсинга.
            parent_html_news_element (str): HTML-тег родительского элемента, содержащего новости.
            parent_html_news_class (str): Класс родительского элемента, содержащего новости.
            html_news_element (str): HTML-тег элемента отдельной новости.
            html_news_class (str): Класс элемента отдельной новости.
            sublink_element (str): HTML-тег ссылки на подстраницу новости.
            sublink_class (str): Класс ссылки на подстраницу новости.
            next_page_link_element (str): HTML-тег ссылки на следующую страницу.
            next_page_link_class (str): Класс ссылки на следующую страницу.
            class_of_news_blocks (str): Класс блока с содержимым новости.
            main_site (str): Главный сайт, необходимый для формирования абсолютных ссылок.
        """ 
        
        self.url = url
        self.parent_html_news_element = parent_html_news_element
        self.parent_html_news_class = parent_html_news_class
        self.html_news_element = html_news_element
        self.html_news_class = html_news_class
        self.sublink_element = sublink_element
        self.sublink_class = sublink_class
        self.next_page_link_element = next_page_link_element
        self.next_page_link_class = next_page_link_class
        self.class_of_news_blocks = class_of_news_blocks
        self._run = True
        self._cnt = 0
        self._soup = None
        self._main_site = main_site
        self.time_html_class = time_html_class
        self.time_html_element = time_html_element
        self._is_first_page = True
    
    def _get_full_link(self, main_site, required_page):
        '''Получение полной ссылки'''
        if not required_page:
            return required_page
        return main_site + required_page
    
    def _get_html_code(self, url):
        '''Получение объекта soup'''
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'lxml')
        except requests.exceptions.ConnectionError as e:
            print(f'Ошибка при подключении подстраницы {url}: {e}')
            return
        return soup
    

    def _html_subpages_parser(self):
        '''Метод для парсинга страницы каждой новости'''
        all_new_body = ''
        news_text = ''
        stop_parsing = False
        for i in self.temp:
            #print(i.text)
            if not TimeUtils.check_time(i, self.time_html_element, self.time_html_class):
                if stop_parsing:
                    self._run = False
                    return all_new_body
                continue

            suburl_tag_href = i.find(self.sublink_element, class_ = self.sublink_class)

            suburl_short = suburl_tag_href['href']
            _suburl = self._get_full_link(self._main_site, suburl_short)

            _subsoup = self._get_html_code(_suburl)
            
            if _subsoup:
                try:
                    new_body = _subsoup.find('div', class_ = 'topic-page__container').find_all('p')
                    label = _subsoup.find('span', class_ = 'topic-body__title') #!!!Обратить внимание!!!
                    print(f'topic of news {label.text}, {self._cnt}')
                except:
                    print(f'Не удалось получить заголовок новости {self._cnt}')
            else:
                print(f'Код подстраницы {_suburl} не был получен')
            
            for news_string in new_body:
                news_text += news_string.text + "\n"
            self._cnt += 1
            #print(f'news_text: {news_text}')
            all_new_body += news_text
            #print(f'all_new_body: {all_new_body}')
            stop_parsing = True
        return all_new_body

    def _get_next_page_link(self):
        '''Вспомогательный метод для получения ссылки на следующую страницу'''
        print('start')
        #print(f'Now page {self.url}')
        if self.next_page_link_element and self.next_page_link_class:
                next_page_link = self._soup.find_all(self.next_page_link_element, class_ = self.next_page_link_class)
                if len(next_page_link) > 1:
                    self.url = self._get_full_link(self._main_site, next_page_link[1]['href'])
                elif self._cnt < 2 and self._is_first_page:
                    self._is_first_page = False
                    self.url = self._get_full_link(self._main_site, next_page_link[0]['href'])
                else:
                    print(f'Ссылка для следующей страницы ресурса {self.url} не была найдена')
                    self._run = False

                #print(self.run)
                #print(f'Next page {self.url}')

    def main_page_parser(self):
        '''Основной метод'''
        news = ''
        while self._run:
            print(self.url)
            try:
                response = requests.get(self.url)
                self._soup = BeautifulSoup(response.text, 'lxml')
            except requests.exceptions.ConnectionError as e:
                print(f'Ошибка при получении html кода главной страницы {self.url}: {e}')
                return
            if self._soup:    
                self.temp = self._soup.find(self.parent_html_news_element, class_ = self.parent_html_news_class).find_all(self.html_news_element, class_ = self.html_news_class)
            else:
                print(f'Код страницы {self.url} не был получен')
            
            #print(self.temp)
            self._get_next_page_link()    
            new = self._html_subpages_parser()
            print(f'new: {new}')
            if new:
                self.file_path = str(Path(__file__).parent) + '/result.txt'
                with open(self.file_path, "a", encoding="utf-8") as f:
                    f.write(new)
                print(f'new: {new}')
            #добавить обработчик ошибок, если new пустой
        print(f'Новостей всего {self._cnt}')
        return new


