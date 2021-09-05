# Автобусы на карте Москвы

Веб-приложение показывает передвижение автобусов на карте Москвы.

<img src="screenshots/buses.gif">

## Как запустить

- Требуется python версии 3.7 или выше
- Скачайте код
- Установите зависимости: `pip install -r requirements.txt`
- Откройте в браузере файл index.html
- Запустите сервер: `python server.py`
- Запустите генератор движения автобусов: `python fake_bus.py`


## Настройки

Внизу справа на странице можно включить отладочный режим логгирования и указать нестандартный адрес веб-сокета.

<img src="screenshots/settings.png">

Настройки сохраняются в Local Storage браузера и не пропадают после обновления страницы. Чтобы сбросить настройки удалите ключи из Local Storage с помощью Chrome Dev Tools —> Вкладка Application —> Local Storage.

Если что-то работает не так, как ожидалось, то начните с включения отладочного режима логгирования.

## Формат данных

Фронтенд ожидает получить от сервера JSON сообщение со списком автобусов:

```js
{
  "msgType": "Buses",
  "buses": [
    {"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"},
    {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "670к"},
  ]
}
```

Те автобусы, что не попали в список `buses` последнего сообщения от сервера будут удалены с карты.

Фронтенд отслеживает перемещение пользователя по карте и отправляет на сервер новые координаты окна:

```js
{
  "msgType": "newBounds",
  "data": {
    "east_lng": 37.65563964843751,
    "north_lat": 55.77367652953477,
    "south_lat": 55.72628839374007,
    "west_lng": 37.54440307617188,
  },
}
```
Генератор движения автобусов посылает данные вида:
```js
{
  "busId": "c790сс", 
  "lat": 55.7500, 
  "lng": 37.600, 
  "route": "120"
}
```
## Параметры CLI сервера
* --bus_port - порт для имитатора автобусов, по-умолчанию =8080
* --browser_port - порт браузера, по-умолчанию = 8000
* --v - настройка логирования, по-умолчанию False - Выключено

## Параметры генератора
* --server - адрес сервера, по-умолчанию = 127.0.0.1:8080
* --routes_number - количество маршрутов, по-умолчанию = 10
* --buses_per_route - количество автобусов на каждом маршруте, по-умолчанию = 5
* --websockets_number - количество открытых веб-сокетов, по-умолчанию = 1    
* --emulator_id - префикс к busId на случай запуска нескольких экземпляров имитатора, по умолчанию пусто
* --refresh_timeout - задержка в обновлении координат сервера, по-умолчанию = 1    
* --v - настройка логирования, по-умолчанию False - Выключено




## Используемые библиотеки

- [Leaflet](https://leafletjs.com/) — отрисовка карты
- [loglevel](https://www.npmjs.com/package/loglevel) для логгирования


## Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
