import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from Web_parser import Parser
import parsers.parser_database.parser_requests as rq

from pathlib import Path
from datetime import date
import logging
import time


class ParserStarter():
    
    def __init__(self):
        self._path = str(Path(__file__).parent) + '/result.txt'
        
    def data_request(self, source_id):
        try:
            self.source_info = rq.get_source_info(source_id)
        except Exception as e:
            print(f'Error in data_request: {e}')
            return
        return self.source_info
    
    def date_generator(self, date_type):
        return date.today().strftime(date_type)
    
    def make_full_link(self, source_link, date_type):
        link_date = self.date_generator(date_type)
        return f'{source_link}/{link_date}'
    
    def start_parsing(self):
        source_id = 1
        required_fields = [
            'source_url', 'date_format', 'parent_html_news_element', 'parent_html_news_class',
            'html_news_element', 'html_news_class', 'sublink_element', 'sublink_class',
            'next_page_link_element', 'next_page_link_class', 'class_of_news_blocks',
            'time_html_class', 'time_html_element'
        ]
        while True:
            source_info = self.data_request(source_id)
            if not source_info:
                print(f'Не удалось получить информацию об источнике с id {source_id}')
                break

            for field in required_fields:
                if not getattr(source_info, field, None):
                    print(f'Отсутствуют данные о ресурсе {source_info.source_url} в блоке {field}')
                    return

            full_link = self.make_full_link(source_info.source_url, source_info.date_format)
            parser = Parser(url = full_link,
                            parent_html_news_element = source_info.parent_html_news_element,
                            parent_html_news_class = source_info.parent_html_news_class,
                            html_news_element = source_info.html_news_element,
                            html_news_class = source_info.html_news_class,
                            sublink_element = source_info.sublink_element,
                            sublink_class = source_info.sublink_class,
                            next_page_link_element = source_info.next_page_link_element, 
                            next_page_link_class = source_info.next_page_link_class,
                            class_of_news_blocks = source_info.class_of_news_blocks,
                            main_site = source_info.source_url,
                            time_html_class = source_info.time_html_class,
                            time_html_element = source_info.time_html_element)
            parser_response = 0
            while True:
                parser_response = parser.main_page_parser(parser_response)
                if type(parser_response) == int:
                    continue
                elif parser_response == False:
                    print('Парсер завершил работу с ошибкой')
                    return False
                elif parser_response == True:
                    print('Парсер успешно завершил работу')
                    break

            #break
            #time.sleep(10)
            source_id += 1
        print('The end')
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    starter = ParserStarter()
    starter.start_parsing()