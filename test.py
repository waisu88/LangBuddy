import g4f


try:
    odpowiedz_ai = g4f.ChatCompletion.create(
    model="gpt-4",
    messages=[
            {"role": "user", "content": "Hello, can I ask a question?"}
        ],
    max_tokens=40,
)
except Exception as e:
    odpowiedz_ai = "Nie ma odpowiedzi"

print(odpowiedz_ai)