def call_ai_model(client, messages, model, max_tokens):
    result = client.chat_completion(
        messages=messages,
        model=model,
        max_tokens=max_tokens
    )
    return result.choices[0].message.content
