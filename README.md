# Создание комнат

Учебный проект на React с использованием React Router и Vite.

## Функциональность

- Главная страница с формой создания комнаты.
- Отправка POST-запроса на Backend.
- Автоматический переход на страницу созданной комнаты.
- Отображение ID комнаты в адресе страницы.

## Используемые технологии

- React
- JavaScript
- React Router
- Vite
- Flask (Backend)
- SQLite

## Запуск Frontend

1. Перейти в папку `Frontend`.
2. Установить зависимости:

   ```bash
   npm install
   ```

3. Запустить проект:

   ```bash
   npm run dev
   ```

## Запуск Backend

1. Перейти в папку `Backend`.
2. Установить зависимости:

   ```bash
   pip install -r requirements.txt
   ```

3. Запустить сервер:

   ```bash
   python app.py
   ```

Frontend работает на `http://localhost:5173/`, Backend — на `http://localhost:5000/`.
