# DVLA Appointment Scraper Bot

A Telegram bot that monitors and scrapes cancelled DVLA appointments, helping users find available slots quickly.

## Features

- 🔍 **Real-time Monitoring**: Continuously monitors DVLA appointment availability
- 📱 **Telegram Integration**: Receive instant notifications via Telegram
- 🚨 **Cancellation Alerts**: Get notified when appointments become available
- 📍 **Location Filtering**: Filter appointments by specific DVLA centers
- ⏰ **Scheduling**: Set up monitoring schedules and frequency
- 📊 **Statistics**: Track appointment availability trends

## Setup

### Prerequisites

- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- DVLA account credentials

### Installation

1. Clone the repository:
```bash
git clone https://github.com/maxbmaapc/dvla-appointment-scraper-bot.git
cd dvla-appointment-scraper-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run the bot:
```bash
python main.py
```

## Configuration

Create a `.env` file with the following variables:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DVLA_USERNAME=your_dvla_username
DVLA_PASSWORD=your_dvla_password
DATABASE_URL=sqlite:///dvla_bot.db
LOG_LEVEL=INFO
```

## Usage

1. Start the bot: `/start`
2. Set your preferences: `/settings`
3. Start monitoring: `/monitor`
4. Check status: `/status`
5. Stop monitoring: `/stop`

## Commands

- `/start` - Initialize the bot
- `/help` - Show available commands
- `/settings` - Configure monitoring preferences
- `/monitor` - Start appointment monitoring
- `/status` - Check current monitoring status
- `/stop` - Stop monitoring
- `/stats` - View appointment statistics

## Project Structure

```
dvla-appointment-scraper-bot/
├── main.py                 # Main bot entry point
├── bot/
│   ├── __init__.py
│   ├── handlers.py         # Telegram command handlers
│   ├── scraper.py          # DVLA scraping logic
│   └── database.py         # Database operations
├── config/
│   └── settings.py         # Configuration management
├── utils/
│   ├── __init__.py
│   └── helpers.py          # Utility functions
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Disclaimer

This bot is for educational purposes. Please ensure you comply with DVLA's terms of service and respect rate limits when scraping their website.

## Support

If you encounter any issues, please open an issue on GitHub or contact the maintainers.