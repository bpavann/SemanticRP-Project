import os
import fitz
import json
import openai
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, render_template, request

app = Flask(__name__)

cred_object = credentials.Certificate('sdkKey.json')
default_app = firebase_admin.initialize_app(cred_object, {
    "databaseURL": "https://semantics-2c7d5-default-rtdb.firebaseio.com/users/Papers"
})

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded."
        
        # Handling the file upload and process it
        file = request.files['file']
        
        # Saving the file to a temporary location
        filename = file.filename
        file_dir = os.path.join('static', 'Files_di')
        os.makedirs(file_dir, exist_ok=True)  # Create the directory if it doesn't exist
        file_path = os.path.join(file_dir, filename)
        file.save(file_path)

        # Processing the PDF file and extract data
        with fitz.open(file_path) as doc:
            abstract_data = {}
            data = []
            metadata = doc.metadata
            title = metadata.get("title", "")
            author = metadata.get("author", "")
            producer = metadata.get("producer", "")

            for page in doc:
                text = page.get_text()
                lines = text.split("\n")
                for i, line in enumerate(lines):
                    if line.lower().startswith("abstract"):
                        j = i + 1
                        abstract = ""
                        while j < len(lines) and not lines[j].lower().startswith(("keywords", "introduction")):
                            abstract += lines[j] + " "
                            j += 1
                        abstract_data[page.number] = abstract
                        break

        ref = db.reference("/users/Papers")
        ref.push(
            {
                "Title": title,
                "Author": author,
                "Producer": producer,
                "Abstract": abstract
            }
        )

        openai.api_key = "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"

        prompt = f"Retrieve the links of research papers related to the following abstract in all www.researchgate.net/search/publication and pubmed.ncbi.nlm.nih.gov website:\n\n{abstract}"

        model_engine = "text-davinci-003"
        response = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            temperature=0.7,
            max_tokens=2048,
            n=1,
            stop=None,
        )

        papers_data = response.choices[0].text.strip()

        # Render the result.html template with the result data
        return render_template('result.html', data=papers_data)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
