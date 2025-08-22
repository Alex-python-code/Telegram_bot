import asyncio
from pathlib import Path
import time
from datetime import date

from app.database.bot_requests import get_source_info

def main():
    source = get_source_info(1)
    print(source.parent_html_news_class)

main()
#asyncio.run(main())
#print(date.today().strftime('%Y/%m/%d'))
#print(str(Path(__file__).parent))