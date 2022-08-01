# Yatube

## Описание

Учебный проект по созданию социальной сети для ведения дневников с возможностью у пользователей создавать учетные записи, публиковать посты, подписываться на авторов, отмечать понравившиеся записи и комментировать посты.

Встроено тестирование на базе Unittest для проверки работоспособности всего проекта (запуск - python manage.py test).

Весь проект написан на Django (в т.ч. frontend) для практики работы с Django ORM, Unittest, шаблонами, CSS, Bootstrap.

## Доступ

Проект запущен на хостинге PythonAnywhere:
- https://abbadon.pythonanywhere.com/
- Админ-зона: https://abbadon.pythonanywhere.com/admin/

## Зависимости
- Перечислены в файле requirements.txt

## Для локального запуска:
1. Клонируйте репозиторий:
```
git clone git@github.com:AbbadonAA/Yatube.git
```
2. Создайте и активируйте виртуальное окружение:
```
python3 -m venv venv
source venv/bin/activate
```
3. Установите зависимости:
```
pip install -r requirements.txt
```
4. В директории yatube выполните команду:
```
python manage.py runserver
```
5. Проект запущен по адресу http://127.0.0.1:8000/

### Автор
Pushkarev Anton

pushkarevantona@gmail.com
