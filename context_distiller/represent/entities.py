import spacy

# Load the spacy model
nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    """
    Extracts entities from a text using spacy.
    """
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "start": ent.start_char,
            "end": ent.end_char,
            "label": ent.label_
        })
    return entities
