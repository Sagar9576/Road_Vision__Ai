import ollama

prompt = """
You are an AI driving assistant.

Cars: 12
Traffic: HIGH
Risk: MEDIUM
Lane Status: CENTER
Traffic Light: GREEN

Rules:
- Give exactly 3 bullet points.
- Maximum 8 words per bullet.
- No explanations.
"""

response = ollama.chat(
    model="phi3",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

print(response["message"]["content"])