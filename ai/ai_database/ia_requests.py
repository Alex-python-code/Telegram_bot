from ai.ai_database.sync_ai_models import Session


def send_compressed_text(list_of_texts):
    with Session() as session:
        try:
            session.add_all(list_of_texts)
            session.commit()

        except Exception as e:
            return e

        return 'Данные записаны успешно'        