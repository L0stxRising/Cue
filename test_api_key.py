# Tests yr API key duhhh....
import sys
import json
import urllib.request
import urllib.error
import requests
import os

def main():
    if len(sys.argv) > 1:
        key = sys.argv[1].strip() 
    else : sys.exit(1)

    req = urllib.request.Request("https://openrouter.ai/api/v1/auth/key")
    req.add_header("Authorization", f"Bearer {key}")
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        json.loads(resp.read().decode("utf-8"))
        print("VALID")
        sys.exit(0)
    except urllib.error.HTTPError as e:
        print("INVALID" if e.code == 401 else f"ERROR:{e.code}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR:{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()