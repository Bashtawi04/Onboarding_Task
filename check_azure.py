from getpass import getpass

from openai import OpenAI

# The address of your deployed Azure service.
ENDPOINT = (
    "https://yahya-onboarding-rag-resource"
    ".services.ai.azure.com/openai/v1/"
)

# The deployment name shown in Foundry.
DEPLOYMENT = "gpt-5.4-mini"

# Ask for the key privately instead of saving it in the code.
api_key = getpass("Paste your Azure API key, then press Enter: ").strip()

if not api_key:
    raise SystemExit("No API key entered. Run the script again.")

with OpenAI(
    base_url=ENDPOINT,
    api_key=api_key,
    timeout=60.0,
    max_retries=0,
) as client:
    print("Connecting to Azure...", flush=True)

    response = client.responses.create(
        model=DEPLOYMENT,
        input="Reply with exactly: Azure connection successful.",
        store=False,
    )

    print("\nModel reply:")
    print(response.output_text)