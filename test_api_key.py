import sys
from openai import OpenAI, AuthenticationError


def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        sys.exit(1)
    key = sys.argv[1].strip()
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)

    try:
        res = client.get("/auth/key", cast_to=object)
        print("VALID")
        sys.exit(0)
    except AuthenticationError:
        print("INVALID")
        sys.exit(1)
    except Exception as e:
        if getattr(e, "status_code", None) == 401 or "401" in str(e):
            print("INVALID")
        else:
            print(f"ERROR:{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()