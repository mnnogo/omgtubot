# omgtubot
Бот для уведомлений об изменении статуса работ студента на omgtu.ru 

Для работы программы нужно создать переменные окружения TELEGRAM_API_TOKEN, TELEGRAM_ID. В файле encryption.py создать функции encrypt(password) и decrypt(password). Также необходима база данных.

Для запуска готового докера (из корневого каталога):
1. изменить переменные окружения в docker-compose.yml
2. docker-compose build
3. docker-compose up

Ссылка на бота: t.me/omgtu_notification_bot
