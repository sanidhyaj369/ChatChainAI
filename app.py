# Importing neccessary libraries
from flask import Flask, request, jsonify, render_template
from langchain_openai import ChatOpenAI
from textblob import TextBlob
import json
import os
import psycopg2

# Initializing the app
app = Flask(__name__)

# Initialize LangChain with some parameters
llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0.2, max_tokens=50)

# Connect to PostgreSQL database
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres',
    password='postgres',
    host='localhost',
    port='5432'
)

cursor = conn.cursor()

# Check if the table exists, if not create it
cursor.execute("""
    CREATE TABLE IF NOT EXISTS prompts (
        prompt_text TEXT,
        response_text TEXT,
        sentiment TEXT
    ) """)

# Defining routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_response', methods=['POST'])
def generate_response():
    try:
        prompt = request.form['prompt']

        # Generate response using LangChain and OpenAI
        response = str(llm.invoke(prompt).dict().get("content"))

        # Perform sentiment analysis on the response
        sentiment_score = TextBlob(response).sentiment.polarity
        sentiment = "positive" if sentiment_score > 0 else "negative" if sentiment_score < 0 else "neutral"

        # Output response and sentiment in JSON format
        output = {'response': response, 'sentiment': sentiment}

        with open('output.json', 'w') as file:
            json.dump(output, file)

        # Store prompt, response, and sentiment in PostgreSQL database
        cursor.execute("INSERT INTO prompts (prompt_text, response_text, sentiment) VALUES (%s, %s, %s)", (prompt, response, sentiment))
        conn.commit()
        
        return jsonify({'response': response, 'sentiment': sentiment})

    except Exception as e:
        error_message = "An error occurred while processing the request: {}".format(str(e))
        return jsonify({'error': error_message}), 500
    
    finally:
        if 'conn' in locals():
            conn.close()


# Running the app
if __name__ == '__main__':
    app.run(debug=True)