import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import base64
from io import BytesIO
from PIL import Image
from pydub import AudioSegment
from pydub.playback import play

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    print(f"OpenAI API Key exists and begins with {openai_api_key[:8]}")
else:
    print("OpenAI API Key does not exist")

openai = OpenAI()

system_message = "You are a helpful assistant for an Airline called FlightAI. "
system_message += "Give short, courteous answers, no more than 1 sentence. "
system_message += "Always be accurate. If you don't know the answer, say so."

ticket_prices = { "london": "$799", "paris": "$899", "tokyo": "$1400", "berlin": "$499" }

def get_ticket_price(destination_city):
    print(f"Tool get_ticket_price called for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")

price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city. Call this whenever you need to know the ticket price, for example when a customer asks 'How much is a ticket to this city'",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}

def book_ticket(destination_city):
    print(f"Return ticket booked to {destination_city}")

book_function = {
    "name": "book_ticket",
    "description": "Book a return ticket to the destination city. Call this whenever you want to book a ticket, for example when a customer confirms their intent to buy a ticket after knowing the ticket price.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": price_function}, {"type": "function", "function": book_function}]

def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    selected_function = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    city = arguments.get("destination_city")
    if selected_function == "get_ticket_price":
        print(f'Calling get_ticket_price for {city}')
        price = get_ticket_price(city)
        response = {
            "role": "tool",
            "content": json.dumps({"destination_city": city, "price": price}),
            "tool_call_id": tool_call.id
        }
    else:
        print(f'Calling book_ticket for {city}')
        book_ticket(city)
        response = {
            "role": "tool",
            "content": f"Return ticket booked to {city}",
            "tool_call_id": tool_call.id
        }
    return response, city

def artist(city):
    image_response = openai.images.generate(
            model="dall-e-3",
            prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city}, in a vibrant pop-art style",
            size="1024x1024",
            n=1,
            response_format="b64_json"
    )
    image_base64 = image_response.data[0].b64_json
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))

def talker(message):
    response = openai.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=message
    )

    audio_stream = BytesIO(response.content)
    audio = AudioSegment.from_file(audio_stream, format="mp3")
    play(audio)

def chat(history):
    messages = [{"role": "system", "content": system_message}] + history
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
    image = None

    if response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        response, city = handle_tool_call(message)
        messages.append(message)
        messages.append(response)
        image = artist(city)
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)

    reply = response.choices[0].message.content
    history += [{"role":"assistant", "content": reply}]

    talker(reply)

    return history, image

with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(height=500, type="messages")
        image_output = gr.Image(height=500)
    with gr.Row():
        entry = gr.Textbox(label="Chat with our AI Assistant:")
    with gr.Row():
        clear = gr.Button("Clear")

    def do_entry(message, history):
        history += [{"role":"user", "content": message}]
        return "", history

    entry.submit(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
        chat, inputs=chatbot, outputs=[chatbot, image_output]
    )
    clear.click(lambda: None, inputs=None, outputs=chatbot, queue=False)

ui.launch(inbrowser=True)
