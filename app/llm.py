from openai import OpenAI

from app.config import settings


client = OpenAI(
    base_url=settings.litellm_base_url,
    api_key=settings.litellm_master_key
)


def generate_answer(question: str, chunks):
    context = "\n\n".join(
        chunk.page_content
        for chunk in chunks
    )

    prompt = f"""
You are a document question-answering assistant.

Answer the question ONLY using the provided document context.

If the answer cannot be found in the context, say:
"I could not find this information in the uploaded document."

Do not make up information.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    response = client.chat.completions.create(
        model=settings.litellm_model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content
