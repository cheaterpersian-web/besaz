# Telegram Bot Manager System

A comprehensive Telegram-based bot management system that allows you to sell bot hosting as a monthly service. Everything is handled directly inside Telegram through menus, inline buttons, and commands - no external website or frontend required.

## Features

### 🤖 Bot Management
- **User Bot Creation**: Users can request their own sub-bots by providing bot tokens
- **Automatic Deployment**: System clones bot code from GitHub and runs it with provided tokens
- **Unlimited Bots**: No limit to number of bots created (each requires subscription)
- **Auto Restart**: Bots automatically restart when main system restarts

### 💳 Subscription System
- **Flexible Plans**: 1 month, 2 months, 3 months (configurable)
- **Manual Payment**: Bank transfer (card-to-card) and cryptocurrency payments
- **Payment Verification**: Users submit payment proof, admin manually verifies
- **Auto Shutdown**: Expired bots automatically stop until payment confirmed

### 📊 Monitoring & Management
- **Real-time Monitoring**: System constantly checks bot status and subscription expiration
- **Admin Panel**: Complete admin interface within Telegram
- **User Panel**: User interface for bot management and payments
- **Statistics**: View all active bots, expiration dates, and system stats

### 🔧 Admin Features
- **User Management**: Add/remove users, manage permissions
- **Payment Approval**: Approve/reject payments manually
- **Price Configuration**: Change subscription prices and durations
- **Broadcast Messages**: Send messages to all bot owners
- **System Control**: Restart bots, cleanup expired bots

## Installation

### Prerequisites
- Python 3.8+
- Git
- VPS or server with internet access

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd telegram-bot-manager
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up your main bot**
   - Create a bot with @BotFather
   - Get your bot token
   - Get your admin user ID
   - Set up a channel for user verification

5. **Configure the system**
   Edit `.env` file with your settings:
   ```env
   MAIN_BOT_TOKEN=your_main_bot_token_here
   ADMIN_USER_ID=your_admin_user_id_here
   MAIN_BOT_ID=your_main_bot_id_here
   LOCKED_CHANNEL_ID=@your_channel_username
   
   # Payment settings
   BANK_CARD_NUMBER=1234567890123456
   CRYPTO_WALLET_ADDRESS=your_crypto_wallet_address
   
   # Subscription plans
   PRICE_1_MONTH=10.00
   PRICE_2_MONTHS=18.00
   PRICE_3_MONTHS=25.00
   ```

6. **Run the system**
   ```bash
   python run.py
   ```

## Usage

### For Users

1. **Start the bot**: Send `/start` to your main bot
2. **Join the channel**: Join the required channel to access the bot
3. **Create a bot**: Use "Create New Bot" and provide your bot token from @BotFather
4. **Subscribe**: Choose a plan and make payment
5. **Submit proof**: Send payment proof (screenshot or transaction ID)
6. **Wait for approval**: Admin will verify and activate your bot

### For Admins

1. **Access admin panel**: Use `/admin` command
2. **Manage users**: View and manage all users
3. **Approve payments**: Review and approve/reject payment submissions
4. **Monitor bots**: View all bots and their status
5. **Configure settings**: Update prices and payment information
6. **System control**: Restart bots, cleanup expired bots

## Commands

### User Commands
- `/start` - Start the bot and see main menu
- `/mybots` - View your bots and their status
- `/subscribe` - Subscribe to a plan
- `/payments` - View payment history
- `/help` - Show help message

### Admin Commands
- `/admin` - Access admin panel
- `/setup` - Initial bot setup
- `/users` - Manage users
- `/broadcast` - Send message to all users

## Database

The system uses SQLite database with the following tables:
- `users` - User information and roles
- `bots` - Bot information and status
- `subscriptions` - Subscription details and expiration
- `payments` - Payment records and status
- `settings` - System configuration

## Bot Template

The system automatically clones and deploys bots from a GitHub repository. The bot template should include:
- Basic bot structure with command handlers
- Environment variable support for bot token
- Requirements.txt for dependencies
- Proper error handling and logging

## Security

- All bot tokens are stored securely in the database
- Admin privileges are required for sensitive operations
- Channel membership verification before bot access
- Manual payment verification system

## Monitoring

The system includes automatic monitoring that:
- Checks bot status every 5 minutes
- Automatically stops expired bots
- Starts bots with active subscriptions
- Notifies users about upcoming renewals
- Cleans up dead processes

## Deployment

### VPS Deployment

1. **Set up VPS**: Ubuntu/Debian recommended
2. **Install Python**: Python 3.8+ with pip
3. **Clone repository**: Git clone your repository
4. **Install dependencies**: pip install -r requirements.txt
5. **Configure environment**: Set up .env file
6. **Run with systemd**: Create systemd service for auto-start
7. **Set up monitoring**: Use systemd or supervisor for process management

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "run.py"]
```

## Troubleshooting

### Common Issues

1. **Bot not starting**: Check bot token validity
2. **Database errors**: Ensure SQLite permissions
3. **Payment not approved**: Check admin notifications
4. **Bot stops unexpectedly**: Check subscription status

### Logs

Check `bot_manager.log` for detailed system logs.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Contact the admin through the bot
- Check the documentation

## Roadmap

- [ ] Webhook support for payments
- [ ] Multiple payment gateways
- [ ] Advanced bot templates
- [ ] API for external integrations
- [ ] Multi-language support
- [ ] Advanced analytics and reporting