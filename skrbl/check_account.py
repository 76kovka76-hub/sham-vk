"""Read-only check: SKRBL group MUST be linked separately in VediSMM."""
import os
import requests

TARGET_ID = "243241856"
BASE = "https://vedismm.ru/api/v1"

def main():
    token = os.getenv("VEDISMM_TOKEN", "").strip()
    if not token:
        raise RuntimeError("VEDISMM_TOKEN not configured")
    response = requests.get(BASE + "/accounts",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=35)
    response.raise_for_status()
    payload = response.json().get("data", [])
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected VediSMM response")
    match = [x for x in payload if
             x.get("network") == "vk" and
             str(x.get("external_id", "")).lstrip("-") == TARGET_ID]
    print("SKRBL connected VK account matches:", len(match))
    print("IMPORTANT: do not substitute the existing SHAM account.")
    if len(match) != 1:
        raise RuntimeError("SKRBL VK 243241856 is NOT connected to this VediSMM token. Link it in VediSMM before test publishing.")
    account = match[0]
    print("SKRBL account ID:", account.get("id"),
          "status:", account.get("status", "not-provided"))
    print("SKRBL_ACCOUNT_CONNECTED=YES")

if __name__ == "__main__":
    main()
