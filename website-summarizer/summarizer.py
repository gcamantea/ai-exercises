import sys
import os
import requests
from ollama import Client
from bs4 import BeautifulSoup
from IPython.display import Markdown, display

if len(sys.argv) < 3:
    print("Usage: python summarizer.py <url> <model>")
    sys.exit(1)

client = Client(host='http://localhost:11434')

WEB_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
}

class Website:
    def __init__(self, url):
        """
        Create this Website object from the given url using the BeautifulSoup library.
        """
        self.url = url
        response = requests.get(url, headers=WEB_HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)

system_prompt = "You are an assistant that analyzes the contents of a website \
and provides a short summary, ignoring text that might be navigation related. \
Respond in markdown."

def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled {website.title}"
    user_prompt += "\nThe contents of this website is as follows; \
please provide a short summary of this website in markdown. \
If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += website.text
    return user_prompt

def messages_for(website):
    return [
        { "role": "system", "content": system_prompt },
        { "role": "user", "content": user_prompt_for(website) }
    ]

def summarize(url, model):
    website = Website(url)
    response = client.chat(model=model, messages=messages_for(website))
    return response['message']['content']

def display_summary(url, model):
    summary = summarize(url, model)
    print(summary)

if __name__ == "__main__":
    url = sys.argv[1]
    model = sys.argv[2]
    display_summary(url, model)
