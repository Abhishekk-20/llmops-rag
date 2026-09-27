from langchain_ollama import ChatOllama

from app.config import settings


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

    llm = ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=0
    )

    response = llm.invoke(prompt)

    return response.content
