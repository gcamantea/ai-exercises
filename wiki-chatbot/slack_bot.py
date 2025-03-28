import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import logging
from chatbot.core import ChatbotCore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class SlackBot:
    def __init__(self):
        load_dotenv()
        self.app = App(token=os.environ["SLACK_BOT_TOKEN"])
        self.chatbot = ChatbotCore(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            kb_id=os.environ['BEDROCK_KNOWLEDGE_BASE_ID']
        )
        self._setup_handlers()

    def _check_thread_parent_mention(self, channel_id, thread_ts, bot_id):
        try:
            parent_message = self.app.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=1
            )["messages"][0]
            return f"<@{bot_id}>" in parent_message.get("text", "")
        except Exception as e:
            logger.error(f"Error checking thread parent message: {str(e)}")
            return False

    def _should_process_message(self, event, is_dm, is_mentioned, is_in_relevant_thread):
        if "bot_id" in event:
            return False
        return is_dm or is_mentioned or is_in_relevant_thread

    def _clean_message_text(self, text, bot_id, is_dm):
        if not is_dm and f"<@{bot_id}>" in text:
            return text.replace(f"<@{bot_id}>", "").strip()
        return text

    def _format_markdown_for_slack(self, text):
        """Convert markdown to Slack-friendly format"""
        # Replace code blocks
        text = text.replace("```", "```\n")  # Ensure newline after code block start
        
        # Basic markdown conversions
        formatting_rules = {
            r'\*\*(.*?)\*\*': '*\\1*',  # Bold: **text** -> *text*
            r'\_([^_]+)\_': '_\\1_',    # Italic: _text_ -> _text_
            r'\`([^\`]+)\`': '`\\1`',   # Inline code: `text` -> `text`
            r'\~\~(.*?)\~\~': '~\\1~',  # Strikethrough: ~~text~~ -> ~text~
            r'\[(.*?)\]\((.*?)\)': '\\1 (\\2)',  # Links: [text](url) -> text (url)
        }
        
        import re
        for pattern, replacement in formatting_rules.items():
            text = re.sub(pattern, replacement, text)
        
        return text

    def _get_conversation_history(self, channel_id, thread_ts):
        """Fetch conversation history from Slack"""
        try:
            logger.info(f"Fetching conversation history for channel: {channel_id}, thread: {thread_ts}")
            
            messages = self.app.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts
            )["messages"]
            
            logger.info(f"Retrieved {len(messages)} messages from thread")
            
            history = []
            bot_id = self.app.client.auth_test()["user_id"]
            
            for msg in messages:
                # Skip any system messages or messages without text
                if "text" not in msg or msg.get("subtype") == "bot_message":
                    continue
                
                text = msg["text"]
                # Clean bot mentions from messages
                if f"<@{bot_id}>" in text:
                    text = text.replace(f"<@{bot_id}>", "").strip()
                
                # Determine message role
                role = "assistant" if msg.get("bot_id") else "user"
                history.append({"role": role, "content": text})
            
            logger.info(f"Processed {len(history)} messages into conversation history")
            
            return history
            
        except Exception as e:
            logger.error(f"Error fetching conversation history: {str(e)}")
            return []

    def _handle_message(self, event, say):
        channel_id = event["channel"]
        message_ts = event.get("ts")
        thread_ts = event.get("thread_ts")
        
        is_dm = event.get("channel_type", "") == "im"
        bot_id = self.app.client.auth_test()["user_id"]
        
        # Check message relevance
        is_in_relevant_thread = thread_ts and self._check_thread_parent_mention(channel_id, thread_ts, bot_id)
        is_mentioned = not is_dm and event.get("text", "") and f"<@{bot_id}>" in event["text"]
        
        if not self._should_process_message(event, is_dm, is_mentioned, is_in_relevant_thread):
            return

        # Process message
        response_thread_ts = thread_ts or message_ts
        user_text = self._clean_message_text(event["text"], bot_id, is_dm)
        
        try:
            # Fetch conversation history from Slack
            history = self._get_conversation_history(channel_id, response_thread_ts)
            
            # Generate response with the fetched history
            response = self.chatbot.generate_response(user_text, history)
            formatted_response = self._format_markdown_for_slack(response)
            say(text=formatted_response, thread_ts=response_thread_ts)
            logger.info("Successfully sent response to Slack")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            say(
                text="I apologize, but I encountered an error while processing your request. Please try again.",
                thread_ts=response_thread_ts
            )

    def _setup_handlers(self):
        self.app.event("message")(self._handle_message)
        self.app.event("ready")(self._ready)

    def _ready(self):
        logger.info("⚡️ Bolt app is ready and running!")

    def start(self):
        logger.info("Starting Slack bot initialization...")
        try:
            handler = SocketModeHandler(self.app, os.environ["SLACK_APP_TOKEN"])
            logger.info("Socket Mode handler created, starting app...")
            handler.start()
        except Exception as e:
            logger.error(f"Error starting Slack bot: {str(e)}")

if __name__ == "__main__":
    bot = SlackBot()
    bot.start() 