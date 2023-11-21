from utils.data import info, dbase, Misc
from utils.encrypt import passManager
from google.api_core import exceptions as api_core
from google.auth import exceptions as auth
from openai import AsyncOpenAI
import os
import openai
import google.generativeai as palm
import json
import random

THIS_PATH = os.path.dirname(os.path.realpath(__file__))
PATH = os.path.dirname(THIS_PATH)

class AIGen:
    def __init__(self, user_id, chat_name):
        self.user_id = user_id
        self.chat_name = chat_name
        with open(f'{PATH}/config.json') as f:
            self.config = json.load(f)
        self.client = AsyncOpenAI(api_key=self.config['GPT_TOKEN'],)
        self.dbase = dbase(self.user_id, self.chat_name)
        self.prompts = info()


    async def getGPT(self, prompt:str):
        LLM = await self.dbase.getLLM
        raw_token = await self.dbase.getGPTToken
        token = await passManager(self.user_id).show(raw_token)
        try:
            client = AsyncOpenAI(api_key=token)
            response = await client.chat.completions.create(
                model=LLM, # gpt-4-1106-preview, gpt-3.5-turbo-1106, gpt-3.5-turbo-16k
                max_tokens=200,
                temperature=0.7,
                messages=prompt
            )
            return response.choices[0].message.content
        except openai.APIConnectionError as e:
            print(e.__cause__)  # an underlying Exception, likely raised within httpx.
            return "**ERROR:** The server could not be reached"
        except openai.RateLimitError as e:
            return "**ERROR:** A 429 status code was received; we should back off a bit."
        except openai.APIStatusError as e:
            print(e.status_code)
            print(e.response)
            return"**ERROR:** Another non-200-range status code was received"




    async def getPALM(self, prompt:str):
        LLM = await self.dbase.getLLM
        raw_token = await self.dbase.getPalmToken
        token = await passManager(self.user_id).show(raw_token)
        try:
            palm.configure(api_key=token)
            defaults = {
            'model': f'models/{LLM}',
            'temperature': 0.7,
            'candidate_count': 1,
            'top_k': 40,
            'top_p': 0.95,
            'max_output_tokens': 250,
            'stop_sequences': ['input:']
            }
            # generate_text gave better results compared to the models available in the '.chat' method
            # in the sense that it is a lot less robotic sounding
            response = palm.generate_text(
            **defaults,
            prompt=prompt
            )
            dummyText = await Misc().getDummyText
            result = response.result or random.choice(dummyText) # if it returns an empty string it was deemed inappropriate, so return a random phrase instead
            return result

        except api_core.InvalidArgument:
            return False, "**The token provided is invalid.** Make sure the token you provided is correct by re-entering."
        except auth.DefaultCredentialsError:
            return False, "**You don't have an active token**."
        except Exception:
            return False, "**Something went wrong:** If you're using the default token, you're likely being ratelimited. You can avoid this by using your own (FREE). "
        



    async def hasProfanity(self, words):
        """Checks if a word/sentence is Inappropriate"""
        response = await self.client.moderations.create(input=words)
        if response.results[0].flagged:
            return True
        else:
            return False
