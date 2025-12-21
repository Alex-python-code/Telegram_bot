from .admin import admin_router
from .common import common_router
from .news import news_router
from .preferences import preferences_router


all_routers = [admin_router, common_router, news_router, preferences_router]
