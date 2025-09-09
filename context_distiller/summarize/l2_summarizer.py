import os
from typing import List
from sqlalchemy.orm import Session
from context_distiller.core.db import Chunk, Summary
from context_distiller.llm.lmstudio_client import LMStudioClient

def load_prompt_template(name: str) -> str:
    """
    Loads a prompt template from the llm/prompts directory.
    """
    # Correctly resolve the path relative to this file's location
    # This is more robust than assuming a fixed current working directory.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_dir = os.path.join(current_dir, '..', 'llm', 'prompts')
    template_path = os.path.join(prompts_dir, name)

    with open(template_path, 'r') as f:
        return f.read()

def generate_l2_summary_for_chunks(chunks: List[Chunk], llm_client: LMStudioClient, session: Session):
    """
    Generates and stores an L2 summary for a list of L0 chunks.
    """
    if not chunks:
        return

    # Combine the text of all L0 chunks
    combined_text = "\n\n---\n\n".join([chunk.text for chunk in chunks])

    # Format the prompt
    prompt_template = load_prompt_template('l2_fusion.txt')
    prompt = prompt_template.format(text_chunks=combined_text)

    messages = [
        {"role": "system", "content": "You are an expert summarization AI."},
        {"role": "user", "content": prompt}
    ]

    # Generate the summary
    summary_text = llm_client.chat(messages=messages, temperature=0.3, max_tokens=500)

    if summary_text:
        # Store the new summary in the database
        new_summary = Summary(
            level=2,
            text=summary_text,
            model="local_llm", # Placeholder for now
            token_len=len(summary_text.split()), # Simple word count for now
            provenance_chunk_ids=[chunk.chunk_id for chunk in chunks]
        )
        session.add(new_summary)
        session.commit()
        print(f"Generated and stored L2 summary for {len(chunks)} chunks.")
    else:
        print("Failed to generate L2 summary.")
