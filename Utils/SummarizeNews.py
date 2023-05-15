# pylint: disable=C0301
# pylint: disable=R0902
# pylint: disable=W0702
# pylint: disable=C0103
"""
OpenAI ChatGPT API implementation to summarize news articles.
"""
import os
import openai
import re
from dotenv import load_dotenv
from tqdm import tqdm
from google.cloud import storage
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Summarize news articles -> GeneratePodcast
class SummarizeNews:
    """
    SummarizeNews object responsible for summarizing all news articles.
    """
    def __init__(self, articles) -> None:
        self.summaries = []
        self.articles = articles
        self.bucket = storage.Client.from_service_account_json('TTSCredentials.json').bucket(os.getenv('BUCKET_NAME_CB'))
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'TTSCredentials.json'

    def summarize_articles(self):
        """
        ChatGPT API call to summarize list of articles.
        """
        for article in tqdm(self.articles):
            try:
                response = openai.ChatCompletion.create(
                    model = 'gpt-3.5-turbo',
                    messages = [
                        {"role": "system", "content": "You summarize news articles about crypto into a script for a podcast."},
                        {"role": "user", "content": os.getenv('OPENAI_PROMPT_CB') + str(article[1])}
                    ],
                    temperature = 0.0
                )
                self.summaries.append(re.sub(r"\$(\d+)K", r"$\1k", response["choices"][0]["message"]["content"]))
            except:
                response = ""
                self.summaries.append("")

        self.summaries = [s for s in self.summaries if s != ""]
        self.log_summaries()
        self.generate_description()
        self.generate_introduction()
        self.generate_outro()

    def log_summaries(self):
        """
        Stores logs of the summaries generated.
        """
        blob = self.bucket.blob('logs/logs_summaries.txt')
        blob.upload_from_string('\n\n'.join(self.summaries).encode('utf-8'), content_type='text/plain; charset=utf-8')

    def generate_description(self):
        """
        Generate a description for the podcast episode.
        """
        headlines = list(map(lambda x: x[0], self.articles))[:3]
        try:
            response = openai.ChatCompletion.create(
                model = 'gpt-3.5-turbo',
                messages = [
                    {"role": "system", "content": "You create a description for a podcast."},
                    {"role": "user", "content": os.getenv('OPENAI_DESCRIPTION_PROMPT_CB') + str(headlines[0]) + '\n' + str(headlines[1]) + '\n' + str(headlines[2]) + '\n'}
                ],
                temperature = 0.0
            )

            blob = self.bucket.blob('podcast_contents/description.txt')
            blob.upload_from_string((response["choices"][0]["message"]["content"]).encode('utf-8'), content_type='text/plain; charset=utf-8')
            blob.make_public()

        except:
            response = "Welcome to today's episode! Have a nice day ahead!"
            blob = self.bucket.blob('podcast_contents/description.txt')
            blob.upload_from_string(response.encode('utf-8'), content_type='text/plain; charset=utf-8')
            blob.make_public()
    
    def generate_introduction(self):
        """
        Generate an intro for the podcast episode.
        """

        headline = list(map(lambda x: x[0], self.articles))[3]
        try:
            response = openai.ChatCompletion.create(
                model = 'gpt-3.5-turbo',
                messages = [
                    {"role": "system", "content": "You create an introduction for a podcast."},
                    {"role": "user", "content": os.getenv('OPENAI_INTRODUCTION_PROMPT_CB')}
                ],
                temperature = 0.85
            )

            blob = self.bucket.blob('podcast_contents/introduction.txt')
            blob.upload_from_string((response["choices"][0]["message"]["content"]).encode('utf-8'), content_type='text/plain; charset=utf-8')

        except:
            response = os.getenv('OPENAI_INTRODUCTION_DEFAULT_CB') + ' ' + headline
            blob = self.bucket.blob('podcast_contents/introduction.txt')
            blob.upload_from_string(response.encode('utf-8'), content_type='text/plain; charset=utf-8')

    def generate_outro(self):
        """
        Generate an outro for the podcast episode.
        """
        try:
            response = openai.ChatCompletion.create(
                model = 'gpt-3.5-turbo',
                messages = [
                    {"role": "system", "content": "You create an outro for a podcast."},
                    {"role": "user", "content": os.getenv('OPENAI_OUTRO_PROMPT_CB')}
                ],
                temperature = 0.85
            )

            blob = self.bucket.blob('podcast_contents/outro.txt')
            blob.upload_from_string((response["choices"][0]["message"]["content"]).encode('utf-8'), content_type='text/plain; charset=utf-8')

        except:
            response = os.getenv('OPENAI_OUTRO_DEFAULT_CB')
            blob = self.bucket.blob('podcast_contents/outro.txt')
            blob.upload_from_string(response.encode('utf-8'), content_type='text/plain; charset=utf-8')

    def get_summaries(self):
        """
        Getter for self.summaries list.
        """
        return self.summaries
    