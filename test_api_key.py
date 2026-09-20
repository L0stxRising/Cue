import sys
import json
import urllib.request
import urllib.error
import os

def main():
    if len(sys.argv) > 1:
        key = sys.argv[1].strip()
    else:
        sys.exit(1)

    req = urllib.request.Request("https://openrouter.ai/api/v1/auth/key")
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("User-Agent",  "Mozilla/5.0")

    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read()
        json.loads(data.decode("utf-8"))
        print("VALID")
        sys.exit(0)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("INVALID")
        else:
            print(f"ERROR:{e.code}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR:{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()