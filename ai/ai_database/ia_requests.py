from ai.ai_database.sync_ai_models import Session
from ai.ai_database.sync_ai_models import News


def send_compressed_text(list_of_texts):
    with Session() as session:
        ready_to_send = []
        for string in list_of_texts:
            ready_to_send.append(News(news_body = string['news_body'],
                                      news_theme = string['news_theme'],
                                      news_time = string['news_time'],
                                      news_date = string['news_date'],
                                      source_group = string['mass_media'],
                                      source_name = string['source_name']
                                      ))
        try:
            session.add_all(ready_to_send)
            session.commit()
        except Exception as e:
            print(f'Ошибка записи в бд: {e}')
            return
        print('Данные записаны в базу')