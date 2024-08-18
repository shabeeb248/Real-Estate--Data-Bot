import base64
import json
import os
import re
import tempfile
import openai
from dotenv import load_dotenv
from os import getenv

import pandas as pd
import requests
load_dotenv()
client = openai.OpenAI()

from pymongo import MongoClient

mclient = MongoClient(getenv("MONGODB_URI"))
db = mclient.samplechatbot
collection = db.main

def create(file):

    details = collection.find_one({})

    if details:
        try:
            client.beta.vector_stores.delete(details["vector_store_id"])
            client.files.delete(details["file_id"])
            client.beta.assistants.delete(details["assistant_id"])
            client.beta.threads.delete(details["thread_id"])
        except:
            pass

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        # Read CSV file into pandas DataFrame
        df = pd.read_csv(file)
        # Write DataFrame to JSON file
        df.to_csv(tmp.name)
        
        temp_file_path = tmp.name

    xfile = client.files.create(file=open(temp_file_path, "rb"), purpose='assistants')
    vs = client.beta.vector_stores.create(name="sample-chatbot", file_ids=[xfile.id])
    thread = client.beta.threads.create()

    assistant = client.beta.assistants.create(
            model="gpt-4o",
            tools=[{"type": "code_interpreter"}],
            tool_resources={
                "code_interpreter":{
                    "file_ids":[xfile.id]
                }
                #"file_search": {
                #    "vector_store_ids": [vs.id]
                #}
            },
            instructions="You are a Real Estate Data Analysis Bot. Answer the following questions as such."
        )
    obj = {
        "chat":[],
        "filename":file.name,
        "assistant_id":assistant.id,
        "file_id":xfile.id,
        "vector_store_id":vs.id,
        "thread_id":thread.id
    }
    collection.delete_many({})
    collection.insert_one(obj)
    return True

def upload_image_to_imgbb(images_bytes):
    url = "https://api.imgbb.com/1/upload"
    
    payload = {
        "key": os.environ.get("IMGBB_KEY"),
        "image": images_bytes
    }
    
    response = requests.post(url, payload)
    result = json.loads(response.text)
    url = result["data"]["url"]
    print(url)
    return url


def get_image_url_and_text(contents):
    image_file_id = contents[0].image_file.file_id
    text = contents[1].text.value
    image_data = client.files.content(image_file_id)
    image_data_bytes = image_data.read()
    image_base64 = base64.b64encode(image_data_bytes).decode('utf-8')
    image_url = upload_image_to_imgbb(image_base64)
    return image_url, text

def answer(question):
    details = collection.find_one({})
    collection.update_one({}, {"$push":{"chat":{"role":"user", "content":question}}})

    try:
        thread = client.beta.threads.retrieve(details["thread_id"])
    except:
        thread = client.beta.threads.create()
        details["thread_id"] = thread.id
        collection.update_one({}, {"$set":{"thread_id":thread.id}})

    run = client.beta.threads.runs.create_and_poll(
        thread_id=details["thread_id"],
        assistant_id=details["assistant_id"],
        instructions="You have been provided a csv file of which the first row corresponds to its columns. \
                            When asked a question related to the data provided, write and run code to answer the question. \
                            Do not ask any confirming questions. Assume all that is necessary. \
                            Do not mention anything insinuating that a file has been uploaded. Answer the following question: " + question,
    )
    print(run)
    messages = client.beta.threads.messages.list(thread_id=details["thread_id"],run_id=run.id)
    print(messages)
    contents = messages.data[0].content
    
    if contents[0].type == "image_file":
        image_url, text = get_image_url_and_text(contents)
        text = text.replace("\n\n", "\n \n")
        text = re.sub(r'【.*?】', '', text)
        collection.update_one({}, {"$push":{"chat":{"image":image_url, "content":text, "role":"assistant"}}})
        return {"image":image_url, "content":text, "role":"assistant"}
    else:
        text = re.sub(r'【.*?】', '', contents[0].text.value)
        text = text.replace("\n", "<br></br>")
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        collection.update_one({}, {"$push":{"chat":{"content":text, "role":"assistant"}}})
        return {"content":contents[0].text.value, "role":"assistant"}

def getchat():
    details = collection.find_one({})
    if details:
        return details["chat"]
    else:
        return []