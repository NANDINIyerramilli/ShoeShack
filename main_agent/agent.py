from main_agent.graph import graph


def main():
    print("Ecommerce Chatbot (type 'quit' to exit)")
    while True:
        query = input("User > ").strip()
        if not query:
            continue
        if query.lower() in {"quit", "exit"}:
            break
        result = graph.invoke({"query": query, "user_id": "user_1"})
        print("\nAssistant >", result["response"], "\n")


if __name__ == "__main__":
    main()
