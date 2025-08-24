import spacy
from spacy.language import Language

# A cache for loaded spacy models
_model_cache = {}

def get_spacy_model(model_name: str = "en_core_web_sm") -> Language:
    """
    Loads a spacy model, caching it for efficiency.
    """
    if model_name not in _model_cache:
        try:
            _model_cache[model_name] = spacy.load(model_name)
        except OSError:
            print(f"Spacy model '{model_name}' not found. Please download it via:\npython -m spacy download {model_name}")
            raise
    return _model_cache[model_name]

def extract_entities(text: str, nlp: Language):
    """
    Extracts named entities from a text using a spacy model.

    :param text: The text to process.
    :param nlp: The loaded spacy Language object.
    :return: A list of spacy Span objects representing the entities.
    """
    if not text or not text.strip():
        return []

    doc = nlp(text)
    return doc.ents
