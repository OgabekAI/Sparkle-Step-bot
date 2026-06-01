# Sparkle Step Bot

A Telegram bot for ordering **Sparkle Stepp** products, built with [aiogram 3](https://docs.aiogram.dev/) and SQLAlchemy (async SQLite).

## Features

- **Multi-language support** — Russian and Uzbek with a dictionary-based translation system.
- **Product catalog** — browse items, view details (photo, description, price), and adjust quantities.
- **Shopping cart** — add/remove items, view totals, clear cart.
- **Order flow** — collect user name, delivery location (Yandex Geocoder), phone number, payment method (card / cash), and optional promo codes.
- **Promo codes** — percentage-based discounts with limited activations.
- **Admin panel** — add / edit / delete products, manage promo codes, complete or cancel orders, view active orders.
- **Throttling middleware** — rate-limits user messages to prevent spam.
- **Error handler** — catches and logs all Telegram API exceptions gracefully.

## Project Structure

```
Sparkle-Step-bot/
├── app.py                          # Entry point — bot startup & dispatcher config
├── settings.py                     # Environment variables (TOKEN, DB, API keys)
├── loader.py                       # Shared Bot instance
├── requirements.txt                # Python dependencies
│
├── database/
│   ├── models.py                   # SQLAlchemy models (User, Item, Cart, Order, PromoCode)
│   ├── requests.py                 # DB queries for users, items, cart, orders
│   └── admin_requests.py           # DB queries for admin operations
│
├── handlers/
│   ├── users/
│   │   ├── main_hand.py            # User-facing handlers (start, ordering, cart, reviews)
│   │   └── admin_private.py        # Admin command handlers
│   └── errors/
│       └── error_handler.py        # Global error handler
│
├── keyboards/
│   ├── inline/
│   │   └── buttons.py              # Inline keyboards (language, cart, payment, promo)
│   └── reply/
│       ├── key.py                   # Reply keyboards (main menu, settings, items)
│       └── admin_key.py             # Admin reply keyboards
│
├── middlewares/
│   └── throttling.py               # Throttling middleware
│
├── translator/
│   └── translations.py             # RU → UZ translation dictionary
│
└── utils/
    ├── notify_admins.py            # Startup notification to admins
    ├── set_bot_commands.py         # Register bot commands
    └── misc/
        └── logging.py              # Logging configuration
```

## Prerequisites

- Python 3.10+
- A Telegram Bot token (from [@BotFather](https://t.me/BotFather))
- Yandex Geocoder API key (for delivery address resolution)

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/OgabekAI/Sparkle-Step-bot.git
   cd Sparkle-Step-bot
   ```

2. **Create a virtual environment and install dependencies:**

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root with the following variables:

   ```env
   TOKEN=<your-telegram-bot-token>
   ADMIN_ID=<comma-separated-admin-telegram-ids>
   DB_LITE=sqlite+aiosqlite:///database.db
   ADMIN_CHAT_ID=<admin-chat-id-for-order-notifications>
   API_KEY_MAPS=<yandex-geocoder-api-key>
   CHAT_ID=<chat-id-for-user-reviews>
   ```

4. **Run the bot:**

   ```bash
   python app.py
   ```

   The database tables are created automatically on first launch.

## Admin Commands

| Command               | Description                          |
| --------------------- | ------------------------------------ |
| `/admin`              | Open admin panel                     |
| `/help`               | Show all admin commands              |
| `/cancel`             | Cancel the current action            |
| `/done`               | Mark orders as completed             |
| `/cancel_order`       | Cancel specific orders               |
| `/delete_all_orders`  | Delete all orders                    |
| `/active_orders_id`   | Show all active order IDs            |
| `/addpromo`           | Add a new promo code                 |
| `/deletepromo`        | Delete a promo code by ID            |
| `/allpromo`           | List all active promo codes          |

## User Commands

| Command   | Description         |
| --------- | ------------------- |
| `/start`  | Start the bot       |

## Technologies

- **aiogram 3.10** — async Telegram Bot framework
- **SQLAlchemy 2.0** + **aiosqlite** — async ORM with SQLite
- **aiohttp** — async HTTP client (Yandex Geocoder API)
- **environs** — environment variable management
- **pydantic** — data validation

## License

This project is provided as-is for educational and internal use.
