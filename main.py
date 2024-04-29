import re

import PyPDF2
import docx2txt
import spacy
from spacy.matcher import Matcher

import constants as cs

from collections import Counter

nlp = spacy.load("en_core_web_lg")
from fastapi import FastAPI, Query
import nltk
import warnings
from pyresparser import ResumeParser

# Install nltk Dependencies
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')


app = FastAPI(
    title="CV Screener",
    description="This is a CV Screener API",
    version="1.0.0")

global inputfile
matcher = Matcher(nlp.vocab)
# Read patterns from file
with open('job-pattern.txt', 'r') as file:
    matcher_patterns = [line.strip() for line in file]

jobmatcher = Matcher(nlp.vocab)
for pattern in matcher_patterns:
    jobmatcher.add("jobtitle", [[
        {"POS": "PROPN", "OP": "?"},  # Optional proper noun before pattern
        {"LOWER": pattern.lower()},  # The original pattern
        {"POS": "PROPN", "OP": "?"}  # Optional proper noun after pattern
    ]])

@app.get('/')
async def index():
    return {"message": "Hello World"}

def extract_name_Spacy(extracted_text, matcher):
    '''
    Helper function to extract name from spacy nlp text

    :param extracted_text: object of `spacy.tokens.doc.Doc`
    :param matcher: object of `spacy.matcher.Matcher`
    :return: string of full name
    '''
    pattern = [cs.NAME_PATTERN]
    matcher = Matcher(nlp.vocab)
    matcher.add('NAME',patterns=pattern)    # matcher.add('NAME', None, pattern)
    matches = matcher(extracted_text)
    for _, start, end in matches:
        span = extracted_text[start:end]
        if 'name' not in span.text.lower():
            return span.text


def extract_job_titles(text):

    doc = nlp(text)
    matches = jobmatcher(doc)
    job_titles = []
    for match_id, start, end in matches:
        job_title = doc[start:end].text
        job_titles.append(job_title)
    if len(job_titles) == 0:
        return None
    else:
        designation = job_titles[0]
    return designation
def extract_name(text):
    pattern = r'([A-Z][a-z]+)\s([A-Z][a-z]+)'
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return None

def cv_matcher(txtin, text):
    rekwl = []

    for j in text:
        for i in txtin:
            if j == i:
                rekwl.append(j)

    if not rekwl:
        return 'Not Found'
    else:
        kmcount = dict(Counter(rekwl))
        skill_matcher = list(kmcount.items())
        return skill_matcher
@app.get('/cv_reader/')

async def cv_reader(path: str = Query(..., alias="path", description="Path to the CV"), txtin: list = Query(default=[],optional=True, alias="txtin", description="Input text")):
        inputfile = open(path, 'rb')
        file_extension=inputfile.name.split('.')[-1]
        if file_extension == 'pdf' or path.split('.')[-1] == 'docx':
            pdftext=[]
            pdftextphone= []

            # creating a pdf file object

            file_extension = str(inputfile.name).split(".")[-1]
            file_name = str(inputfile.name).split("\\")[-1]
            if file_extension == "pdf":
                # creating a pdf reader object
                pdfReader = PyPDF2.PdfReader(inputfile)

                txt2=[]
                for page in pdfReader.pages:
                    txt1= page.extract_text()
                    txt2.append(str(txt1))

                    # Extracting email addresses.
                    txt3 = re.findall('\S+@\S+', txt1)
                    txt31 = re.findall('[a-zA-Z0–9. _%+-]+@[a-zA-Z0–9. -]+\. [a-zA-Z]{2,}', txt1)
                    txt32 = re.findall('\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', txt1)
                    if txt3 != []:
                        pdftext.append(txt3)
                    if txt31 != []:
                        pdftext.append(txt31)
                    if txt32 != []:
                        pdftext.append(txt32)
                    # Extracting phone numbers
                    txt4= re.findall('\+\d{1,3}\s?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', txt1)
                    txt41 = re.findall('((?:9[679]|8[035789]|6[789]|5[90]|42|3[578]|2[1-689])|9[0-58]|8[1246]|6[0-6]|5[1-8]|4[013-9]|3[0-469]|2[70]|7|1)(?:\W*\d){0,13}\d$', txt1)
                    txt42 = re.findall('\+?(\d[h|\(\d{3}\)|\.|\-|\d]{4,}\d)', txt1)
                    txt43 = re.findall('^(\+\d{1,3})?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', txt1)
                    if txt4 != []:
                        pdftextphone.append(txt4)
                    if txt41 != []:
                        pdftextphone.append(txt41)
                    if txt42 != []:
                        pdftextphone.append(txt42)
                    if txt43 != []:
                        pdftextphone.append(txt43)
                    result = set(map(tuple, pdftext))
                    result2 = set(map(tuple,pdftextphone))

                # Extracting name using Regex
                matcher = Matcher(nlp.vocab)
                pattern = [cs.NAME_PATTERN]
                matcher.add('NAME', patterns=pattern)
                Name_Spacy = nlp(str(txt2))
                name = extract_name_Spacy(Name_Spacy, matcher)

                #Extracting designation

                designation = extract_job_titles(str(txt2))

                ##### getting skills via pyresparser
                # Ignore any user warnings during parsing
                warnings.filterwarnings("ignore", category=UserWarning)

                # Set the path to the PDF file
                resume_path = path

                # Create a ResumeParser object
                parser = ResumeParser(resume_path)

                # Extract the parsed data
                data = parser.get_extracted_data()
                skills = data['skills']
                # designation=data['designation']

                # skills matcher
                stxt=str(txt2)
                mtxt = re.sub('[^A-Za-z0-9]+', ' ', stxt)
                splits = mtxt.split()
                splits = [x.lower() for x in splits]
                txtin = [x.lower() for x in txtin]
                skill_matcher=cv_matcher(txtin, splits)
            ############################################################################
            # Working on Docx files
            elif file_extension == "docx":
                Docx_reader = docx2txt.process(inputfile)

                # Extracting Emails from DOCx
                for word in Docx_reader:

                    text1 = re.findall('\S+@\S+', Docx_reader)
                    text2 = re.findall('[a-zA-Z0–9. _%+-]+@[a-zA-Z0–9. -]+\. [a-zA-Z]{2,}', Docx_reader)
                    text3 = re.findall('\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', Docx_reader)
                    if text1 != []:
                        pdftext.append(text1)
                    if text2 != []:
                        pdftext.append(text2)
                    if text3 != []:
                        pdftext.append(text3)
                    # Extracting phone numbers from DOCx
                    txt4 = re.findall('\+\d{1,3}\s?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', Docx_reader)
                    txt41 = re.findall('((?:9[679]|8[035789]|6[789]|5[90]|42|3[578]|2[1-689])|9[0-58]|8[1246]|6[0-6]|5[1-8]|4[013-9]|3[0-469]|2[70]|7|1)(?:\W*\d){0,13}\d$',Docx_reader)
                    txt42 = re.findall('\+?(\d[h|\(\d{3}\)|\.|\-|\d]{4,}\d)', Docx_reader)
                    txt43 = re.findall('^(\+\d{1,3})?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', Docx_reader)
                    if txt4 != []:
                        pdftextphone.append(txt4)
                    if txt41 != []:
                        pdftextphone.append(txt41)
                    if txt42 != []:
                        pdftextphone.append(txt42)
                    if txt43 != []:
                        pdftextphone.append(txt43)
                # Extracting name:
                matcher = Matcher(nlp.vocab)
                pattern = [cs.NAME_PATTERN]
                matcher.add('NAME', patterns=pattern)
                Name_Spacy = nlp(Docx_reader)
                name = extract_name_Spacy(Name_Spacy, matcher)

                result = set(map(tuple, pdftext))
                result2 = set(map(tuple, pdftextphone))

                # Extract designation

                designation = extract_job_titles(Docx_reader)
                # getting skills via pyresparser
                # Ignore any user warnings during parsing
                warnings.filterwarnings("ignore", category=UserWarning)

                # Set the path to the PDF file
                resume_path = path

                # Create a ResumeParser object
                parser = ResumeParser(resume_path)

                # Extract the parsed data
                data = parser.get_extracted_data()
                skills = data['skills']

                # CV_Skills_matcher
                stxt = str(Docx_reader)
                mtxt = re.sub('[^A-Za-z0-9]+', ' ', stxt)
                splits = mtxt.split()
                splits = [x.lower() for x in splits]
                txtin = [x.lower() for x in txtin]
                skill_matcher = cv_matcher(txtin, splits)
            else:
                raise ValueError("Unsupported file format. Only PDF and DOCX files are supported.")

            return {'name': name, 'email':result, 'phone': result2, 'skills': skills, 'file_name': file_name, 'designation': designation, 'skill_matcher': skill_matcher}

        else:
            return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
