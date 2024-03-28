import re
import os
from flask import request
import PyPDF2
import docx2txt
from models import resume
import constants as cs
import spacy
from spacy.matcher import Matcher
nlp = spacy.load("en_core_web_lg")
from fastapi import FastAPI, Query, Request

app = FastAPI(
    title="CV Screener",
    description="This is a CV Screener API",
    version="1.0.0")

global inputfile
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
def extract_name(text):
    pattern = r'([A-Z][a-z]+)\s([A-Z][a-z]+)'
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return None

@app.get('/cv_reader/')
# async def get_path(path:str):
#     # path = os.getcwd()+path
#     file = open(path, 'r')
#     file_extension=file.name.split('.')[-1]
#     return {"path": path, 'file_extension':file_extension}
async def cv_reader(path: str = Query(..., alias="path", description="Path to the CV")):
        inputfile = open(path, 'rb')
        file_extension=inputfile.name.split('.')[-1]
        if file_extension == 'pdf' or path.split('.')[-1] == 'docx':
            pdftext=[]
            pdftextphone= []
            # creating a pdf file object
            # inputfile = open(path, 'r')
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
                # name= extract_name(str(txt2))
                matcher = Matcher(nlp.vocab)
                pattern = [cs.NAME_PATTERN]
                matcher.add('NAME', patterns=pattern)
                Name_Spacy = nlp(str(txt2))
                name = extract_name_Spacy(Name_Spacy, matcher)
                # name = str(txt2)



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

                # name = (re.findall(r'([A-Z][a-z]+)\s([A-Z][a-z]+)',str(Docx_reader)))[0]
                # name = str(Docx_reader)
            else:
                raise ValueError("Unsupported file format. Only PDF and DOCX files are supported.")


            # resume(name=name, email=str(result), phone=list(result2), skills=None, file_name=file_name)
            return {'name': name, 'email':result, 'phone': result2, 'skills': None, 'file_name': file_name}

        else:
            return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
