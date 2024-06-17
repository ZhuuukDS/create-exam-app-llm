from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
groq_api = os.getenv('groq_api_key')


# functin to open a file and return its contents as a string
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

def chatgpt_qroq_version(user_input, system_message, conversation_history):
    """
    Function to send a query to Groq's model and get the response.
    """
    # initialize Groq client
    client = Groq(api_key=groq_api)
    messages = [{'role': 'system', 'content': system_message}] + conversation_history + [{'role': 'user', 'content': user_input}]

    # perform the chat completion request
    chat_completion = client.chat.completions.create(
        model='llama3-8b-8192',
        messages=messages,
        temperature=0.5,
        top_p=1,
        max_tokens = 4096,
    )
    response_content = chat_completion.choices[0].message.content
    return response_content


def user_chatbot_conversation(system_message, user_topics, user_input):
    conversation_history = []
    system_message = system_message
    conversation_history.append({'role': 'user', 'content': "This is the list of topics for exam:  " + user_topics})

    chatbot_response = chatgpt_qroq_version(user_input, system_message, conversation_history)
    conversation_history.append({'role': 'assistant', 'content': chatbot_response})

    if len(conversation_history) > 40:
        conversation_history = conversation_history[-40:]
    return chatbot_response


def get_mcq():
    user_topics = open_file('user_topics.txt')
    user_input = "Create 20 multiple choice questions with 4 answer options for each, having only 1 correct answer. Indicate correct answer under each question"
    system_message = open_file('system_message_mcq.txt')

    with open("chat_mcq.txt", 'w', encoding="utf-8") as f:
        print(user_chatbot_conversation(system_message, user_topics, user_input), file=f)


def get_owq():
    user_topics = open_file('user_topics.txt')
    user_input = "Create exactly 8 open-written questions. For each question add a correct answer with 2-3 sentences."
    system_message = open_file('system_message_owq.txt')
    with open("chat_owq.txt", 'w', encoding="utf-8") as f:
        print(user_chatbot_conversation(system_message, user_topics, user_input), file=f)
