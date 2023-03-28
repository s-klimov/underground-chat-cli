
```commandline
listen-minechat.py --host minechat.dvmn.org --port 5000 --history ~/minechat.history
```

# Подключаемся к подпольному чату Майнкрафт

Сервис для подключения к чату обмена кодами Майнкрафт

## Приступая к работе

Следуя этим инструкциям, вы получите копию проекта, которая будет запущена на вашем локальном компьютере для целей разработки и тестирования. Примечания о том, как развернуть проект в действующей системе, см. в разделе Развертывание.

### Предпосылки

Клонируйте проект на локальный компьютер

```commandline
git clone https://github.com/s-klimov/underground-chat-cli.git
```

Для работы сервиса у вас должны быть установлены:
* python версии 3.10 и выше
* poetry версии 1.4.x

### Установка проекта

1. Установите зависимости
```commandline
poetry install
```
2. Активируйте локальное окружение
```commandline
poetry shell
```
4. Переименуйте файл .env.dist в .env и заполните его параметрами подключения. Пример:
* MINECHAT_HOST=minechat.dvmn.org
* MINECHAT_PORT=5000
* HISTORY_FILE=chat.txt


## Запуск проекта

Запустите проект
```commandline
python listen-minechat.py --host minechat.dvmn.org --port 5000 --history ~/minechat.history
```
В качестве альтернативы вы можете указать свои параметры подключения при запуске:
```commandline
python listen-minechat.py --host minechat.dvmn.org --port 5000 --history ~/minechat.history
```
Чтобы получить справку по параметрам:
```commandline
python listen-minechat.py --help
```

## Используемый стек

* [asyncio](https://docs.python.org/3/library/asyncio.html) - The library to write concurrent code using the async/await syntax used  
* [poetry](https://python-poetry.org/docs/) - Dependency Management

## Авторы

* **Sergei Klimov** - [repos](https://github.com/s-klimov/)

## Лицензия

Проект разработан под лицензией MIT - см. [LICENSE](LICENSE) файл для подробного изучения.

## Благодарности

* [dvmn.org](https://dvmn.org/modules/)
