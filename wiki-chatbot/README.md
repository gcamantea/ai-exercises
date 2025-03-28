# Slack Wiki Bot

A Slack bot that uses AWS Bedrock and LangChain to answer questions based on your knowledge base content. The bot maintains conversation history within threads and can be used in both direct messages and channels. The architecture is modular, allowing the core chatbot functionality to be used in different interfaces beyond Slack.

## Features

- RAG (Retrieval-Augmented Generation) using AWS Bedrock and Knowledge Bases
- Conversation history maintained within Slack threads
- Supports both direct messages and channel interactions
- Context-aware responses using conversation history
- Responds to mentions in channels and continues conversations in threads
- Detailed logging for debugging

## Prerequisites

- Python 3.8+
- AWS Account with Bedrock access
- Slack Workspace with admin access
- AWS Knowledge Base set up with your content
- AWS CLI configured or AWS credentials

## Project Structure

The project is organized into two main components:

- `chatbot/core.py`: Core chatbot functionality that handles:
  - AWS Bedrock integration
  - LangChain chains and retrievers
  - Conversation history management
  - Response generation
  
- `slack_bot.py`: Slack-specific integration that:
  - Handles Slack events and message processing
  - Manages bot mentions and thread interactions
  - Uses the core chatbot to generate responses

This separation allows the core chatbot to be reused in different interfaces (web, CLI, etc.) while keeping the Slack-specific code isolated.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/slack-wiki-bot.git
cd slack-wiki-bot
```

2. Create the project structure:
```bash
mkdir chatbot
touch chatbot/__init__.py
```

3. Install dependencies using pipenv:
```bash
pipenv install
```

4. Copy the example environment file and fill in your values:
```bash
cp .env.example .env
```

5. Set up your Slack App:
   - Create a new app at https://api.slack.com/apps
   - Enable Socket Mode
   - Add the following Bot Token Scopes:
     - `chat:write` (for sending messages)
     - `im:write` (for thread operations in DMs)
     - `app_mentions:read` (for detecting mentions)
     - `channels:history` (for reading channel messages)
     - `groups:history` (for reading private channel messages)
     - `im:history` (for reading DMs)
     - `mpim:history` (for reading group DMs)
   - Enable Event Subscriptions and subscribe to:
     - `message.im` (for DM events)
     - `message.channels` (for public channel events)
     - `message.groups` (for private channel events)
     - `app_mentions` (for mention events)
   - Install the app to your workspace
   - Copy the Bot User OAuth Token and App-Level Token to your `.env` file

6. Configure AWS:
   - Ensure you have AWS credentials configured (either via AWS CLI or environment variables)
   - Set up a Knowledge Base in Bedrock
   - Add the Knowledge Base ID to your `.env` file

## Usage

1. Start the Slack bot:
```bash
pipenv run python slack_bot.py
```

2. Interact with the bot:
   - In DMs: Send any message
   - In channels: Mention the bot using @BotName
   - Continue conversations in threads
   - The bot maintains context within threads for follow-up questions

## Using the Core Chatbot

The core chatbot can be used independently of Slack. Here's a basic example:

```python
from chatbot.core import ChatbotCore

chatbot = ChatbotCore(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    kb_id="your-knowledge-base-id"
)

# Generate a response
conversation_id = "unique-conversation-id"
response = chatbot.generate_response(conversation_id, "Your question here")
print(response)
```

## Environment Variables

- `SLACK_BOT_TOKEN`: Your Slack bot user OAuth token (starts with `xoxb-`)
- `SLACK_APP_TOKEN`: Your Slack app-level token (starts with `xapp-`)
- `BEDROCK_KNOWLEDGE_BASE_ID`: Your AWS Bedrock Knowledge Base ID
- `AWS_REGION`: (Optional) AWS region for Bedrock services
- AWS credentials (if not using AWS CLI configuration):
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_SESSION_TOKEN` (if using temporary credentials)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Powered by [AWS Bedrock](https://aws.amazon.com/bedrock/)
- Uses [Slack Bolt](https://slack.dev/bolt-python/tutorial/getting-started) 