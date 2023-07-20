<h1 align="center">🔔 DTU Seat Alert Bot 🎓</h1>

<p align="center">
  <img src="./DTUSeatAlertBotImages/seatalertbotimage.png" alt="Bot Logo" width="200">
</p>

<p align="center">
  Welcome to <strong>DTU Seat Alert Bot</strong>, your personal assistant for staying updated on available seats in DTU subjects.
</p>

## Table of Contents
- [About](#about)
- [Features](#features)
- [Commands](#commands)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Getting Started](#getting-started)
- [Deploying on AWS EC2](#deploying-on-aws-ec2)
- [Contributing](#contributing)
- [License](#license)

## About
**DTU Seat Alert Bot** is a Telegram bot designed to provide real-time updates on available seats in various subjects offered by DTU (Delhi Technological University). Whether you are a student looking for open seats to register in a subject or someone who wants to stay informed about seat availability, this bot has got you covered!

## Features
- Get real-time updates on available seats in DTU subjects.
- Subscribe to receive notifications for specific subject codes.
- Unsubscribe from seat notifications.
- Search for the number of available seats in a particular subject.
- User-friendly interface and easy-to-use commands.

## Commands
The following commands are available to interact with the bot:

👋 <b>/start -</b> Start the bot and initiate the conversation.

📚 <b>/seats -</b> Check for the availability of new seats in subjects.

🔔 <b>/update -</b> Subscribe to receive notifications for a specific subject code.

🚫 <b>/revoke -</b> Revoke your subscription to seat notifications.

🔎 <b>/search -</b> Get the number of available seats in a specific subject. Enter the subject code after the command.

✏️ <b>/register -</b> Register yourself for subject exchange. Provide your give and take values for subjects you are willing to give and take.

🚫 <b>/unregister -</b> Unregister yourself from subject exchange. Remove your registration and information from the exchange list.

💡 <b>/exchange -</b> Check if there is any match for you to exchange subjects based on your give and take values.

🔗 <b>/addwa -</b> To add the whatsapp link of the subject code.

🔗 <b>/getwa -</b> To get the whatsapp link of the subject code.

## Usage
1. Start the bot by sending the <b>/start</b> command.
2. Use the <b>/seats</b> command to check for new available seats.
3. Subscribe to receive notifications for a specific subject code using the <b>/update</b> command followed by the subject code.
4. Use the <b>/revoke</b> command to unsubscribe from seat notifications.
5. Search for the number of available seats in a subject using the <b>/search</b> command followed by the subject code.

## Screenshots

|      **Start**      |     **Seats**      | 
|-------------------------|-----------------------|
| ![Start](./DTUSeatAlertBotImages/start.jpeg) | ![seats](./DTUSeatAlertBotImages/seats.jpeg) |

|      **Update**      |     **Search**      |
|-------------------------|-----------------------|
| ![update](./DTUSeatAlertBotImages/update.jpeg) | ![search](./DTUSeatAlertBotImages/search.jpeg) |

## Getting Started
To get started with the **DTU Seat Alert Bot**, follow these steps:

1. Clone the repository.
2. Install the required dependencies.
3. Obtain your Telegram bot token from the BotFather and update the token in the configuration file.
4. Run the bot.
5. Start interacting with the bot on Telegram.

## Deploying on AWS EC2
To deploy the DTU Seat Alert Bot on **AWS EC2**.

## Contributing
Contributions are welcome! Feel free to open issues and submit pull requests to contribute to this project.

## License
This project is licensed under the [MIT License](LICENSE).
