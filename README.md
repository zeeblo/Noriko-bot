# Noriko (discord chatbot)

<img src=".\assets\info\setup_readme_imgs\noriko.png" alt="noriko">

### Basic Overview about Noriko

Noriko doesn't fancy following boring rules or listening to people but deep down has a compassionate side, especially when she sees someone going through something. She mostly grew up as an orphan but apparently that doesn't matter to her, it was a lesson for her to become stronger. Despite her innocent looking demeanor she'll occasionally swear like a sailor and find the strangest things funny.


### Key features
- Freely converse (As much as the AI model allows it)
- Will randomly send you a DM
- Private threads to converse
- Settings to change AI model (once more are added)

### requirements

- Python 3.8 or higher
- `pip install discord.py`
- `pip install openai`
- `pip install -U google-generativeai`
- `pip install better_profanity`
- `pip install cryptography`



# Setup

1. You need a config.json file in the main directory (Also make a new folder and name it 'data')

<img src=".\assets\info\setup_readme_imgs\config.png" alt="config">

2. To get your PaLM API token visit this link https://developers.generativeai.google/products/palm

<img src=".\assets\info\setup_imgs\palm\step1.png" alt="palm api key">

3. If you see this screen then the API might not be available in your region (or you're not signed in), check if it is here: https://developers.generativeai.google/available_regions

<img src=".\assets\info\setup_imgs\palm\step.png" alt="missing access screen">

4. generate a secret key using the cryptographer module and copy the output
```py
from cryptography.fernet import Fernet

key = Fernet.generate_key()

print(str((key), 'utf-8'))
```

5. Enter all your tokens

<img src=".\assets\info\setup_readme_imgs\tokens.png" alt="tokens">


6. Run the bot and you should be good to go.



# Demos

### PaLM - text-bison-001

<img src=".\assets\info\setup_readme_imgs\convo1.png" alt="PaLM API test">


### GPT3

<img src=".\assets\info\setup_readme_imgs\convo3.png" alt="gpt3 api test">

### GPT4

<img src=".\assets\info\setup_readme_imgs\convo2.png" alt="gpt4 api test">