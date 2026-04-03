from paperqa import ask

from bootstrap import build_settings

settings = build_settings()

while True:
    q = input("\nQuestion (or quit): ").strip()
    if q.lower() == "quit":
        break
    response = ask(q, settings=settings)
    print("\n" + response.session.formatted_answer)
