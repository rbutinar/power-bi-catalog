import base64
import json

#carica il token dallo stesso file usato dal test REST, ovvero da .pbi_token_cache.json

import json
TOKEN_PATH = ".pbi_token_cache.json"
try:
    with open(TOKEN_PATH, "r") as f:
        token_data = json.load(f)
    ACCESS_TOKEN = token_data.get("access_token", "")
    print(f"[DEBUG] Token caricato da {TOKEN_PATH}")
except Exception as e:
    print(f"[ERRORE] Impossibile caricare il token da {TOKEN_PATH}: {e}")
    ACCESS_TOKEN = ""

def decode_jwt(token):
    parts = token.split('.')
    if len(parts) != 3:
        return None
    payload = parts[1] + '=' * (-len(parts[1]) % 4)
    decoded = base64.urlsafe_b64decode(payload)
    return json.loads(decoded)

# Inserisci qui il tuo token (solo per debug locale!)
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSIsImtpZCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSJ9.eyJhdWQiOiJodHRwczovL2FuYWx5c2lzLndpbmRvd3MubmV0L3Bvd2VyYmkvYXBpIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvZjY2MDA5ZjktM2FhZS00YTRlLTkxNjEtOTc0YjYzZTdlYjZhLyIsImlhdCI6MTc0NzI0ODEwMCwibmJmIjoxNzQ3MjQ4MTAwLCJleHAiOjE3NDcyNTcxNTcsImFjY3QiOjAsImFjciI6IjEiLCJhaW8iOiJBWFFBaS84WkFBQUFBMXZnVDdNUjBtY1dGWU1USkltUHVwWXZPVVhxNEtiYnkwdHUva3UzUS9HU2NJRkxkdHo0MC8wYTdFNXozUExCdGtNYVBLZ042cjNpSnlBaW1XSkVyRnE0ZEpzM2pkVnFCR0t5anl4UGpaMUl3M3l6TG03WkdhQkpUQWVpRDU3enFxMnlBdnpKZFRINjBjclJwZkQwSGc9PSIsImFtciI6WyJwd2QiLCJtZmEiXSwiYXBwaWQiOiJkMzU5MGVkNi01MmIzLTQxMDItYWVmZi1hYWQyMjkyYWIwMWMiLCJhcHBpZGFjciI6IjAiLCJmYW1pbHlfbmFtZSI6IkJ1dGluYXIiLCJnaXZlbl9uYW1lIjoiUm9iZXJ0byIsImlkdHlwIjoidXNlciIsImlwYWRkciI6IjIuMzYuOTAuMTMzIiwibmFtZSI6IlJvYmVydG8gQnV0aW5hciIsIm9pZCI6ImVmMTI5YjJjLTkxYTAtNDY0OC04ZGM5LWY0NjZkMDg2N2NlZiIsInB1aWQiOiIxMDAzMjAwMzZERkI4RTJGIiwicmgiOiIxLkFhNEEtUWxnOXE0NlRrcVJZWmRMWS1mcmFna0FBQUFBQUFBQXdBQUFBQUFBQUFDdUFGYXVBQS4iLCJzY3AiOiJ1c2VyX2ltcGVyc29uYXRpb24iLCJzaWQiOiIwMDRlNzYwOS1jMTdhLTJiMTMtOGJmYS05ZDgyMTVjYTllZTQiLCJzdWIiOiJLRmJmd1Y3Q244aEtiZFpOZ2p2N0FGcUFndHlDZ2NaT1pOTGFESnhZYUxBIiwidGlkIjoiZjY2MDA5ZjktM2FhZS00YTRlLTkxNjEtOTc0YjYzZTdlYjZhIiwidW5pcXVlX25hbWUiOiJyb2JlcnRvLmJ1dGluYXJAenY3OGQub25taWNyb3NvZnQuY29tIiwidXBuIjoicm9iZXJ0by5idXRpbmFyQHp2NzhkLm9ubWljcm9zb2Z0LmNvbSIsInV0aSI6IkRJR2NUS3AtY2tpSThVOWhvcnNvQUEiLCJ2ZXIiOiIxLjAiLCJ3aWRzIjpbIjYyZTkwMzk0LTY5ZjUtNDIzNy05MTkwLTAxMjE3NzE0NWUxMCIsImZlOTMwYmU3LTVlNjItNDdkYi05MWFmLTk4YzNhNDlhMzhiMSIsIjI3NDYwODgzLTFkZjEtNDY5MS1iMDMyLTNiNzk2NDNlNWU2MyIsImYwMjNmZDgxLWE2MzctNGI1Ni05NWZkLTc5MWFjMDIyNjAzMyIsIjcyOTgyN2UzLTljMTQtNDlmNy1iYjFiLTk2MDhmMTU2YmJiOCIsImYyZWY5OTJjLTNhZmItNDZiOS1iN2NmLWExMjZlZTc0YzQ1MSIsIjY5MDkxMjQ2LTIwZTgtNGE1Ni1hYTRkLTA2NjA3NWIyYTdhOCIsIjI5MjMyY2RmLTkzMjMtNDJmZC1hZGUyLTFkMDk3YWYzZTRkZSIsImYyOGExZjUwLWY2ZTctNDU3MS04MThiLTZhMTJmMmFmNmI2YyIsImI3OWZiZjRkLTNlZjktNDY4OS04MTQzLTc2YjE5NGU4NTUwOSJdLCJ4bXNfaWRyZWwiOiIxIDE0In0.BPXVttJh4_INURCUizCKFQ8Ge5p3RML1NJFnNjyISIc0zNom5xlVtWJQtun7ZHjR5JX8Ivlynxp-gR6QPohCsrdu11uwwMyqPm1laTVw2q9w77EATHwWN65Q-UxHr1joijMBupb_p7X7lvb6afNItDNe2eOeJL15jnu42mOdTPM1Wq68jHnMd0JUV1y_WLUZ2G0lNg5acvFdNjv_nAKnEEElbjZUX607TXcnrEvk5pc4FcdRPv-CJi4Jf7wetP8YXSt92Lp79j71agAlGnITa_hbrGorGl40TCdScqNFB19rdCl5lfho5XGn8fRxobXUASeCLHK2ESpS-nCDNhvoZQ"
payload = decode_jwt(access_token)
print(json.dumps(payload, indent=2))