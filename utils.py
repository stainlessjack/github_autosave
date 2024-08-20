import configparser
import os
import logging
import datetime
from openai import OpenAI

def load_config():
    """Load configuration from the config file specified in the environment variable."""
    config = configparser.ConfigParser()
    config_file = os.environ.get('GITHUB_AUTOSAVE_CONFIG_FILE')
    if not config_file:
        logging.error("GITHUB_AUTOSAVE_CONFIG_FILE environment variable not set.")
        raise EnvironmentError("GITHUB_AUTOSAVE_CONFIG_FILE environment variable not set.")
    config.read(config_file)
    return config['DEFAULT']

def generate_ai_message(changes, openai_key):
    """Generate a commit message using OpenAI based on the changes."""
    client = OpenAI(api_key=openai_key)
    prompt = f"Generate a concise commit message for the following changes:\n{changes}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are one of the best coding mentors in the world."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Failed to generate AI message: {e}")
        return f"Autosave commit at {datetime.datetime.now()}"