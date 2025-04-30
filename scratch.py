import spacy
nlp = spacy.load("en_core_web_sm")

query = "Landry out of bounds bad pass turnover"
doc = nlp(query)
for ent in doc.ents:
    if ent.label_ == "PERSON":
        print(ent.text) 

