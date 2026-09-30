# 📱 Booking Mini App

<p>
  <a href="https://github.com/sonoyumi/booking-miniapp/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/sonoyumi/booking-miniapp/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white">
  <img alt="Telegram Mini App" src="https://img.shields.io/badge/Telegram-Mini%20App-2CA5E0?logo=telegram&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

**🇬🇧 [English](#en)** · **🇮🇹 [Italiano](#it)** · **🇺🇦 [Українська](#uk)** · **🇷🇺 [Русский](#ru)**

---

<a name="en"></a>

## 🇬🇧 English

A Telegram Mini App for [booking-bot](https://github.com/sonoyumi/booking-bot): instead of pressing buttons in the chat,
the customer opens a real booking screen inside Telegram (services, days with free places, times, "my bookings").
The Mini App **uses booking-bot as a library**: the same schedule rules, the same database, the same services file.
A time booked in the chat disappears from the Mini App and vice versa, and the bot's reminders work for both.

```
Telegram ──opens──► index.html + app.js ──fetch /api/* with "Authorization: tma <initData>"──► FastAPI
                     (Telegram theme,        │ signature checked with the bot token            │
                      MainButton, BackButton)│                                                  ▼
                                             └──────────── booking-bot: Schedule · Database · services.json
```

### Features

- **Telegram login without passwords:** every request carries Telegram's signed `initData`; the server recomputes the
  HMAC-SHA256 signature with the bot token and checks its age. The user id comes only from the verified signature.
- **Same rules as the bot:** `Schedule.is_bookable` rejects forged times (10:07, closed days, too far ahead); the database's
  unique index rejects a second booking of the same slot (HTTP 409, the screen reloads the free times).
- **Limits:** at most N upcoming bookings per person; customers cancel only their own bookings.
- **Owner notifications** in Telegram for bookings and cancellations made in the Mini App.
- **Native look:** colors from the user's Telegram theme, Telegram's MainButton, BackButton, haptic feedback and confirm dialog.
  Plain HTML, CSS and JavaScript, no build step.
- **Menu button:** `booking-miniapp set-menu-button` puts "Book" next to the chat's input field.
- **Developer mode:** `DEV_USER_ID` lets you open the page in a normal browser without Telegram (never on a server).

### Quick start

```bash
git clone https://github.com/sonoyumi/booking-miniapp.git
cd booking-miniapp
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"                        # installs booking-bot from GitHub as a dependency
cp .env.example .env                           # BOT_TOKEN and the paths to the bot's database and services
booking-miniapp serve --port 8080
```

Telegram opens Mini Apps only over **HTTPS**: in production put it behind nginx with a certificate and set `WEBAPP_URL`;
for development use a tunnel (for example `cloudflared tunnel --url http://localhost:8080`). Then run
`booking-miniapp set-menu-button`.

Tests: `pytest` (29 tests: the signature algorithm computed by hand, tampered and expired logins, every API endpoint with a
fixed clock, double booking, forged times, limits, notifications, the bot and the Mini App sharing one database, static
files, and `node --check` of the front-end script).

### Project structure

```
src/booking_miniapp/
├── auth.py      # Telegram initData validation (HMAC-SHA256, age)
├── api.py       # FastAPI: /api/config, days, slots, bookings; static files
├── notify.py    # owner notifications
├── config.py    # settings from .env (same schedule variables as booking-bot)
├── cli.py       # booking-miniapp serve | set-menu-button
└── static/      # index.html, style.css, app.js (Telegram WebApp SDK)
```

### Author

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)), Python developer: Telegram bots, web scraping, automation.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-profile-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/vladyslav-shokun/)

> 💼 Want an app for your customers without an app store? Get in touch, I'll build it as a Telegram Mini App.

### License

MIT, see [LICENSE](LICENSE).

---

<a name="it"></a>

## 🇮🇹 Italiano

**[🇬🇧 English](#en)** · **🇮🇹 Italiano** · **[🇺🇦 Українська](#uk)** · **[🇷🇺 Русский](#ru)**

Una Telegram Mini App per [booking-bot](https://github.com/sonoyumi/booking-bot): invece di premere pulsanti in chat, il cliente
apre una vera schermata di prenotazione dentro Telegram (servizi, giorni con posti liberi, orari, «le mie prenotazioni»).
La Mini App **usa booking-bot come libreria**: stesse regole dell'orario, stesso database, stesso file dei servizi. Un orario
prenotato in chat sparisce dalla Mini App e viceversa, e i promemoria del bot funzionano per entrambi.

### Funzionalità

- **Accesso con Telegram senza password:** ogni richiesta porta l'`initData` firmato da Telegram; il server ricalcola la firma
  HMAC-SHA256 con il token del bot e ne controlla l'età. L'id dell'utente arriva solo dalla firma verificata.
- **Stesse regole del bot:** `Schedule.is_bookable` rifiuta orari falsificati (10:07, giorni chiusi, troppo avanti); l'indice
  univoco del database rifiuta una seconda prenotazione dello stesso orario (HTTP 409, la schermata ricarica gli orari liberi).
- **Limiti:** al massimo N prenotazioni future a persona; ognuno annulla solo le proprie.
- **Notifiche al titolare** su Telegram per prenotazioni e annullamenti fatti nella Mini App.
- **Aspetto nativo:** colori dal tema Telegram dell'utente, MainButton, BackButton, vibrazione e dialogo di conferma di Telegram.
  HTML, CSS e JavaScript semplici, senza build.
- **Pulsante menu:** `booking-miniapp set-menu-button` mette «Prenota» accanto al campo di testo della chat.
- **Modalità sviluppo:** `DEV_USER_ID` permette di aprire la pagina in un browser normale senza Telegram (mai sul server).

### Avvio rapido

```bash
git clone https://github.com/sonoyumi/booking-miniapp.git
cd booking-miniapp
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"                        # installa booking-bot da GitHub come dipendenza
cp .env.example .env                           # BOT_TOKEN e i percorsi del database e dei servizi del bot
booking-miniapp serve --port 8080
```

Telegram apre le Mini App solo in **HTTPS**: in produzione mettetela dietro nginx con certificato e impostate `WEBAPP_URL`;
per lo sviluppo usate un tunnel (per esempio `cloudflared tunnel --url http://localhost:8080`). Poi `booking-miniapp set-menu-button`.

Test: `pytest` (29 test: l'algoritmo della firma calcolato a mano, accessi manomessi e scaduti, ogni endpoint con un orologio
fisso, doppia prenotazione, orari falsificati, limiti, notifiche, bot e Mini App sullo stesso database, file statici e
`node --check` dello script front-end).

### Struttura del progetto

```
src/booking_miniapp/
├── auth.py      # verifica dell'initData di Telegram (HMAC-SHA256, età)
├── api.py       # FastAPI: /api/config, giorni, orari, prenotazioni; file statici
├── notify.py    # notifiche al titolare
├── config.py    # impostazioni da .env (stesse variabili dell'orario di booking-bot)
├── cli.py       # booking-miniapp serve | set-menu-button
└── static/      # index.html, style.css, app.js (Telegram WebApp SDK)
```

### Autore

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)), sviluppatore Python: bot Telegram, web scraping, automazione.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-profile-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/vladyslav-shokun/)

> 💼 Volete un'app per i vostri clienti senza passare dagli store? Scrivetemi, la realizzo come Telegram Mini App.

### Licenza

MIT, vedi [LICENSE](LICENSE).

---

<a name="uk"></a>

## 🇺🇦 Українська

**[🇬🇧 English](#en)** · **[🇮🇹 Italiano](#it)** · **🇺🇦 Українська** · **[🇷🇺 Русский](#ru)**

Telegram Mini App для [booking-bot](https://github.com/sonoyumi/booking-bot): замість натискати кнопки в чаті, клієнт
відкриває справжній екран запису всередині Telegram (послуги, дні з вільними місцями, час, «мої записи»). Mini App
**використовує booking-bot як бібліотеку**: ті самі правила розкладу, та сама база, той самий файл послуг. Час, зайнятий
у чаті, зникає з Mini App і навпаки, а нагадування бота працюють для обох.

### Можливості

- **Вхід через Telegram без паролів:** кожен запит несе підписаний Telegram `initData`; сервер перераховує підпис
  HMAC-SHA256 токеном бота й перевіряє вік. Id користувача береться лише з перевіреного підпису.
- **Ті самі правила, що в боті:** `Schedule.is_bookable` відхиляє підроблений час (10:07, вихідні, надто далеко);
  унікальний індекс бази відхиляє другий запис на той самий час (HTTP 409, екран оновлює вільний час).
- **Обмеження:** не більше N майбутніх записів на людину; кожен скасовує лише свої.
- **Сповіщення власнику** в Telegram про записи й скасування з Mini App.
- **Рідний вигляд:** кольори з теми Telegram користувача, MainButton, BackButton, вібровідгук і діалог підтвердження Telegram.
  Звичайні HTML, CSS і JavaScript без збирання.
- **Кнопка меню:** `booking-miniapp set-menu-button` ставить «Записатися» поруч із полем введення в чаті.
- **Режим розробки:** `DEV_USER_ID` дає відкрити сторінку у звичайному браузері без Telegram (ніколи на сервері).

### Швидкий старт

```bash
git clone https://github.com/sonoyumi/booking-miniapp.git
cd booking-miniapp
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"                        # встановлює booking-bot з GitHub як залежність
cp .env.example .env                           # BOT_TOKEN і шляхи до бази та послуг бота
booking-miniapp serve --port 8080
```

Telegram відкриває Mini App лише через **HTTPS**: на сервері — за nginx із сертифікатом і `WEBAPP_URL`; для розробки —
тунель (наприклад, `cloudflared tunnel --url http://localhost:8080`). Потім `booking-miniapp set-menu-button`.

Тести: `pytest` (29 тестів: алгоритм підпису, порахований вручну, підроблені й прострочені входи, кожен ендпоінт із
фіксованим годинником, подвійний запис, підроблений час, ліміти, сповіщення, бот і Mini App на одній базі, статичні
файли й `node --check` фронтенд-скрипту).

### Структура проєкту

```
src/booking_miniapp/
├── auth.py      # перевірка initData від Telegram (HMAC-SHA256, вік)
├── api.py       # FastAPI: /api/config, дні, час, записи; статичні файли
├── notify.py    # сповіщення власнику
├── config.py    # налаштування з .env (ті самі змінні розкладу, що в booking-bot)
├── cli.py       # booking-miniapp serve | set-menu-button
└── static/      # index.html, style.css, app.js (Telegram WebApp SDK)
```

### Автор

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)) — Python-розробник: Telegram-боти, парсинг, автоматизація.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-profile-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/vladyslav-shokun/)

> 💼 Потрібен застосунок для клієнтів без магазинів застосунків? Напишіть мені, зроблю його як Telegram Mini App.

### Ліцензія

MIT — див. [LICENSE](LICENSE).

---

<a name="ru"></a>

## 🇷🇺 Русский

**[🇬🇧 English](#en)** · **[🇮🇹 Italiano](#it)** · **[🇺🇦 Українська](#uk)** · **🇷🇺 Русский**

Telegram Mini App для [booking-bot](https://github.com/sonoyumi/booking-bot): вместо того чтобы нажимать кнопки в чате,
клиент открывает настоящий экран записи внутри Telegram (услуги, дни со свободными местами, время, «мои записи»).
Mini App **использует booking-bot как библиотеку**: те же правила расписания, та же база, тот же файл услуг. Время,
занятое в чате, исчезает из Mini App и наоборот, а напоминания бота работают для обоих.

### Возможности

- **Вход через Telegram без паролей:** каждый запрос несёт подписанный Telegram `initData`; сервер пересчитывает подпись
  HMAC-SHA256 токеном бота и проверяет возраст. Id пользователя берётся только из проверенной подписи.
- **Те же правила, что в боте:** `Schedule.is_bookable` отклоняет подделанное время (10:07, выходные, слишком далеко);
  уникальный индекс базы отклоняет вторую запись на то же время (HTTP 409, экран обновляет свободное время).
- **Ограничения:** не больше N будущих записей на человека; каждый отменяет только свои.
- **Уведомления владельцу** в Telegram о записях и отменах из Mini App.
- **Родной вид:** цвета из темы Telegram пользователя, MainButton, BackButton, виброотклик и диалог подтверждения Telegram.
  Обычные HTML, CSS и JavaScript без сборки.
- **Кнопка меню:** `booking-miniapp set-menu-button` ставит «Записаться» рядом с полем ввода в чате.
- **Режим разработки:** `DEV_USER_ID` позволяет открыть страницу в обычном браузере без Telegram (никогда на сервере).

### Быстрый старт

```bash
git clone https://github.com/sonoyumi/booking-miniapp.git
cd booking-miniapp
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"                        # ставит booking-bot с GitHub как зависимость
cp .env.example .env                           # BOT_TOKEN и пути к базе и услугам бота
booking-miniapp serve --port 8080
```

Telegram открывает Mini App только по **HTTPS**: на сервере — за nginx с сертификатом и `WEBAPP_URL`; для разработки —
туннель (например, `cloudflared tunnel --url http://localhost:8080`). Потом `booking-miniapp set-menu-button`.

Тесты: `pytest` (29 тестов: алгоритм подписи, посчитанный вручную, подделанные и просроченные входы, каждый эндпоинт
с фиксированными часами, двойная запись, подделанное время, лимиты, уведомления, бот и Mini App на одной базе,
статические файлы и `node --check` фронтенд-скрипта).

### Структура проекта

```
src/booking_miniapp/
├── auth.py      # проверка initData от Telegram (HMAC-SHA256, возраст)
├── api.py       # FastAPI: /api/config, дни, время, записи; статические файлы
├── notify.py    # уведомления владельцу
├── config.py    # настройки из .env (те же переменные расписания, что в booking-bot)
├── cli.py       # booking-miniapp serve | set-menu-button
└── static/      # index.html, style.css, app.js (Telegram WebApp SDK)
```

### Автор

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)) — Python-разработчик: Telegram-боты, парсинг, автоматизация.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-profile-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/vladyslav-shokun/)

> 💼 Нужно приложение для клиентов без магазинов приложений? Напишите мне, сделаю его как Telegram Mini App.

### Лицензия

MIT — см. [LICENSE](LICENSE).
