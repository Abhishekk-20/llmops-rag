import time

from openai import OpenAI

from app.config import settings
from app.metrics import (
    llm_requests_total,
    llm_request_latency_seconds,
    llm_ttft_seconds,
    llm_prompt_tokens_total,
    llm_completion_tokens_total,
    llm_tokens_total,
    llm_estimated_cost_usd_total,
    llm_last_request_estimated_cost_usd,
)


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

    llm_requests_total.inc()

    start_time = time.perf_counter()
    first_token_recorded = False

    answer_parts = []
    usage = None

    try:
        stream = client.chat.completions.create(
            model=settings.litellm_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            stream=True,
            stream_options={
                "include_usage": True
            }
        )

        for chunk in stream:

            # Capture token usage
            if chunk.usage is not None:
                usage = chunk.usage

            # Some streaming chunks do not contain choices
            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if content:

                # Record Time To First Token
                if not first_token_recorded:

                    ttft = time.perf_counter() - start_time

                    llm_ttft_seconds.observe(ttft)

                    first_token_recorded = True

                answer_parts.append(content)

        # ====================================================
        # TOKEN + COST METRICS
        # ====================================================

        if usage is not None:

            prompt_tokens = usage.prompt_tokens or 0
            completion_tokens = usage.completion_tokens or 0
            total_tokens = usage.total_tokens or 0

            # Token metrics
            llm_prompt_tokens_total.inc(prompt_tokens)
            llm_completion_tokens_total.inc(completion_tokens)
            llm_tokens_total.inc(total_tokens)

            # Cost calculation
            input_cost = (
                prompt_tokens
                / 1_000_000
                * settings.llm_input_cost_per_million_tokens
            )

            output_cost = (
                completion_tokens
                / 1_000_000
                * settings.llm_output_cost_per_million_tokens
            )

            request_cost = input_cost + output_cost

            # Prometheus cost metrics
            llm_estimated_cost_usd_total.inc(request_cost)

            llm_last_request_estimated_cost_usd.set(
                request_cost
            )

        return "".join(answer_parts)

    finally:

        duration = time.perf_counter() - start_time

        llm_request_latency_seconds.observe(duration)
