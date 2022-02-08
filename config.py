from os import getenv
from sys import exit
# айди админа
admin_id = getenv('ADMIN_ID')
if not admin_id:
    exit('Ошибка - нет админского айди')
# токен бота
bot_token = getenv("HOT_TOURS_BOT_TOKEN")
if not bot_token:
    exit("Ошибка - нет токена для бота.")
# реферальная ссылка тур - агенства, без нее сайт не выдает данные. Добывается у сайта
referer = getenv('REFERER')
if not referer:
    exit('Оператор не задан')
# логин от базы данных
db_login = getenv('DB_LOGIN')
if not db_login:
    exit('Логин базы данных не задан')
# пароль от базы данных
db_pass = getenv('DB_PASS')
if not db_pass:
    exit('Пароль базы данных не задан')