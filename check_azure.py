"""Check that the configured Azure chat deployment responds."""

from openai import OpenAI

from onboarding.config import ENDPOINT, CHAT_MODEL, get_api_key


def main():
    print(f"Endpoint: {ENDPOINT}")
    print(f"Chat deployment: {CHAT_MODEL}")

    api_key = get_api_key()

    with OpenAI(
        base_url=ENDPOINT,
        api_key=api_key,
        timeout=60.0,
        max_retries=0,
    ) as client:
        print("Connecting to Azure...", flush=True)

        response = client.responses.create(
            model=CHAT_MODEL,
            input="Reply with exactly: Azure connection successful.",
            store=False,
        )

        answer = (response.output_text or "").strip()

        if not answer:
            raise RuntimeError("Azure returned no text.")

        print("\nModel reply:")
        print(answer)


if __name__ == "__main__":
    main()