from openai import OpenAI
import time
from datetime import datetime
import json
import re

from ai.ai_database.sync_ai_models import News
from ai.ai_database.ia_requests import send_compressed_text

from config import AI_TOKEN


class Ai:
    def __init__(self, path_file_with_news, max_execution_time):
        self.file_path = path_file_with_news
        self.client = OpenAI(api_key=AI_TOKEN)
        self.max_execution_time = max_execution_time
        self.attempt_download = 0

    def file_sender(self):
        with open(self.file_path, "rb") as f:
            uploaded_file = self.client.files.create(file=f, purpose="batch")
        print(f"ID загруженного файла: {uploaded_file.id}")
        return uploaded_file.id

    def start_batch_job(self):
        batch = self.client.batches.create(
            input_file_id=self.file_sender(),
            endpoint="/v1/chat/completions",
            completion_window=self.max_execution_time,
        )
        print(f"ID запущенной batch задачи: {batch.id}")
        self.status_checker(batch.id)

    def status_checker(self, batch_id):
        while True:
            status = self.client.batches.retrieve(batch_id)

            if status.status in ["validating", "queued", "in_progress"]:
                print(f"Статус: {status.status}")
                time.sleep(30)
                continue

            elif status.status == "completed":
                print(f"Задача batch завершена успешно: {datetime.now()}")
                self.get_response(status.output_file_id)
                return
            else:
                print(
                    f"Задача batch id {status.id} завершена с ошибкой: {datetime.now()}, статус: {status.status}"
                )
                print(f"Причина ошибки: {status}")
                return

    def get_response(self, output_file_id):
        try:
            response = self.client.files.content(output_file_id)
            print(f"Тип файла response: {type(response)}")
            print(f"Файл: {output_file_id} успешно скачан")
        except Exception as e:
            print(f"Не удалось скачать файл: {output_file_id} ошибка: {e}")
            if self.attempt_download < 3:
                self.get_response(output_file_id)
            return False
        self.responses_to_dict(response.text)
        return True

    def responses_to_dict(self, response_of_jsonl):
        list_of_responses = [
            json.loads(line) for line in response_of_jsonl.splitlines() if line.strip()
        ]
        print("Файл успешно был конвервертирован в список словарей")
        self.parsing_ai_responses(list_of_responses)

    def parsing_ai_responses(self, list_of_responses):
        send_to_db = []
        for json_obj in list_of_responses:
            ai_text = json_obj["response"]["choices"][0]["message"]["content"]
            tag_pattern = r'--тег\s*"([^"]+)"'
            tag_of_new = re.search(tag_pattern, ai_text).group(1)
            print(f"Тип файла ai_text{type(ai_text)}")
            text_of_news = ai_text.replace(tag_of_new + " ", "")
            send_to_db.append(News(news_body=text_of_news, news_theme=tag_of_new))

        completed_status = send_compressed_text(send_to_db)
        print(completed_status)
