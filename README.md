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

### Развертывание

1. Установите зависимости
```commandline
poetry install
```
2. Активируйте локальное окружение
```commandline
poetry shell
```
4. Скопируйте файл .env.dist в .env и заполните его параметрами подключения.  

Назначение параметров:
* HOST -- хост сервера с чатом
* PORT -- порт сервера с чатом
* HISTORY -- путь к файлу для хранения истории чата
* ACCOUNT -- хэш аккаунта для написания сообщений в чат
* DISPLAY -- адрес виртуального дисплея для X-сервера (используется при запуске скрипта gui.py из контейнера)

Пример:  
* HOST=minechat.dvmn.org
* PORT=5000
* HISTORY=chat.txt
* ACCOUNT=f007e00c-cd77-11ed-ad76-0242ac110002
* DISPLAY=172.26.32.1:0.0

5. Настройте запуск скрипта gui.py (если запускаете из контейнера)
[Видеоинструкция](https://youtu.be/W82jvmiaDtk?list=PLQMlgM71Ag24wooZwLXguA_Cx7rRXaVwa)
Пример запуска экранного сервера из ОС Windows:
```commandline
PS C:\Program Files (x86)\Xming> .\xming -ac
```

## Запуск проекта

### Запустите скрипт прослушивания чата
```commandline
python listen_minechat.py
```
В качестве альтернативы вы можете указать свои параметры подключения при запуске:
```commandline
python listen_minechat.py --host minechat.dvmn.org --port 5000 --history ~/minechat.history
```
Чтобы получить справку по параметрам:
```commandline
python listen_minechat.py --help
```

### Запустите скрипт написания сообщения в чат
```commandline
python sender.py --port 5050 --message 'Напишите сюда сообщение'
```
> порт для написания сообщения в чат должен отличаться от порта, указываемого для пролсушивания чата  
В качестве альтернативы вы можете указать свои параметры подключения при запуске:
```commandline
python sender.py --host minechat.dvmn.org --port 5050 --account f007e00c-cd77-11ed-ad76-0242ac110002 --message 'Напишите сюда сообщение'
```
Можно одновременно зарегистрировать нового пользователя и отправить от его имени сообщение:
```commandline
python sender.py --host minechat.dvmn.org --port 5050 --register 'Cool Bot' --message 'Напишите сюда сообщение'
```
После успешной регистрации пользователя его учетная запись сохраняется в файле users.json:
```commandline
cat users.json
```
Параметр скрипта sender.py register имеет `приоритет` над параметром `account`.  
Чтобы получить справку по параметрам:
```commandline
python sender.py --help
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
