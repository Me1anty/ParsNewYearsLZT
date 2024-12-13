cookies = {

}

headers = {

}
BASE_URL = "https://lolz.live/threads/7927875"
TOTAL_PAGES = 263
DELAY = 0.5
MAX_RETRIES = 3
RETRY_DELAY = 5

import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Tuple
import time
import os
from datetime import datetime


STANDARD_STYLES = {
    'style218': 'АМС нов',
    'style9': 'Дизайнер',
    'style349': 'Редактор',
    'style365': 'Редактор нов',
    'style350': 'Главный дизайнер',
    'style354': 'Рекламный менеджер',
    'style371': 'Команда чатов Telegram',
    'style29': 'Куратор',
    'style30': 'Арбитр',
    'style4': 'Модератор',
    'style12': 'Главный Модератор',
    'style353': 'Главный арбитр',
    'style11': 'Продавец на форуме',
    'style65': 'Привилегии на маркете',
    'style22': 'Постоялец',
    'style23': 'Эксперт',
    'style60': 'Гуру',
    'style351': 'ИИ',
    'style359': 'Спонсор',
    'style7': 'Кодер',
    'style8': 'Суприм',
    'style26': 'Легенда',
    'style21': 'Местный',
    'style2': 'Новорег',
    'style18': 'Арбитраж',
}

class ForumParser:
    def __init__(self, cookies: dict, headers: dict):
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.session.cookies.update(cookies)
        self.results_dir = f'results_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.makedirs(self.results_dir, exist_ok=True)
        self.file_handles = {}
        self.processed_users = set()
        
        groups = list(set(STANDARD_STYLES.values()))
        groups.extend(['Уникальные', 'Забаненные'])
        
        for group in groups:
            self.file_handles[group] = open(f'{self.results_dir}/{group}.txt', 'a', encoding='utf-8')

    def __del__(self):
        for handle in self.file_handles.values():
            handle.close()

    def get_page_content(self, url: str, current_try: int = 1) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"\nОшибка при получении страницы (попытка {current_try}/{MAX_RETRIES}): {e}")
            
            if current_try < MAX_RETRIES:
                print(f"Ожидание {RETRY_DELAY} секунд перед повторной попыткой...")
                time.sleep(RETRY_DELAY)
                return self.get_page_content(url, current_try + 1)
            else:
                print(f"Достигнуто максимальное количество попыток для {url}")
                return None

    def extract_user_info(self, post) -> Tuple[Optional[str], Optional[str], bool]:
        username_elem = post.find('a', class_='username')
        if not username_elem:
            return None, None, False


        if 'banned' in username_elem.get('class', []):
            return username_elem.text.strip(), 'Забаненные', False


        username = username_elem.text.strip()
        style_spans = username_elem.find_all('span', class_=re.compile(r'style\d+'))
        

        for span in style_spans:
            for class_name in span.get('class', []):
                if class_name in STANDARD_STYLES:
                    return username, STANDARD_STYLES[class_name], False
        

        if style_spans or username_elem.find('span', {'style': True}):
            return username, 'Уникальные', True
            
        return username, 'Местный', False

    def save_user(self, username: str, group: str):
        if not username or not group:
            return

        if username not in self.processed_users:
            user_str = f"@{username}\n"
            self.file_handles[group].write(user_str)
            self.file_handles[group].flush()
            self.processed_users.add(username)
            print(f"[{group}] @{username}")

    def parse_user_data(self, html_content: str, page: int):
        if not html_content:
            print(f"\nНе удалось получить содержимое страницы {page}. Пропускаем...")
            return

        soup = BeautifulSoup(html_content, 'html.parser')
        message_list = soup.find(id='messageList')
        if not message_list:
            return

        print(f"\nОбработка страницы {page}/{TOTAL_PAGES}:")
        for post in message_list.find_all('li', id=re.compile(r'post-\d+')):
            username, group, is_unique = self.extract_user_info(post)
            if username and group:
                self.save_user(username, group)

def main():
    parser = ForumParser(cookies, headers)
    
    try:
        for page in range(1, TOTAL_PAGES + 1):
            url = f"{BASE_URL}/page-{page}" if page > 1 else BASE_URL
            
            html_content = parser.get_page_content(url)
            if html_content:
                parser.parse_user_data(html_content, page)
            
            if page < TOTAL_PAGES:
                time.sleep(DELAY)
    
    except KeyboardInterrupt:
        print("\nПарсинг прерван пользователем")
    finally:
        print(f"\nПарсинг завершен. Результаты сохранены в директории '{parser.results_dir}'")
        print(f"Всего обработано пользователей: {len(parser.processed_users)}")

if __name__ == "__main__":
    main()
