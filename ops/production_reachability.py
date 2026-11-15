"""Read-only status probe for the public PMS Bersoch desktop and mobile URLs.

Only certifies HTTP landing page HTML and expected app branding. It cannot certify
app functions, releases, data freshness, Apps Script or end-to-end deployments.
Do not silently succeed on exceptions or sleeping/identity gateways.
"""
import json
import sys
import urllib.error
import urllib.request

TARGETS = (
    ("BERSOCH_DESKTOP", "https://pms-max.streamlit.app/", "streamlit", "Streamlit"),
    ("BERSOCH_MOBILE", "https://pms-bersoch-mobile.netlify.app/", "mobile", "PMS Bersoch"),
)


def classify_response(kind, status, content, final_url):
    text = content.decode("utf-8", errors="replace")
    address = str(final_url).lower()
    if any(marker in address for marker in ("/login", "/auth", "accounts.google.com")):
        return "INCONCLUSIVE_GATEWAY"
    if status != 200:
        return "ERROR_HTTP"
    if not text.strip():
        return "ERROR_EMPTY_RESPONSE"
    if "<html" not in text.lower() and "<!doctype html" not in text.lower():
        return "ERROR_NOT_HTML"
    if kind == "streamlit":
        if "streamlit" not in text.lower():
            return "INCONCLUSIVE_UNRECOGNIZED_HTML"
        return "REACHABLE_HTML_NOT_FUNCTIONALITY"
    if "PMS Bersoch" not in text:
        return "INCONCLUSIVE_UNRECOGNIZED_HTML"
    return "REACHABLE_HTML_NOT_FUNCTIONALITY"


def probe(name, url, kind, expected_name, opener=urllib.request.urlopen):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 PMS-Reachability/2.0"})
    try:
        with opener(req, timeout=25) as response:
            body = response.read(1_200_000)
            status = response.status
            final_url = response.url
        classification = classify_response(kind, status, body, final_url)
        return {"name": name, "url": url, "final_url": final_url, "http_status": status,
                "status": classification, "bytes": len(body)}
    except urllib.error.HTTPError as exc:
        state = "INCONCLUSIVE_GATEWAY" if exc.code in (302, 303, 401, 403) and kind == "streamlit" else "ERROR_HTTP"
        return {"name": name, "url": url, "http_status": exc.code, "status": state}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {"name": name, "url": url, "status": "ERROR_NETWORK",
                "detail": type(exc).__name__ + ": " + str(exc)[:120]}


def exit_code(results):
    states = [x["status"] for x in results]
    if any(x.startswith("ERROR_") for x in states):
        return 1
    if any(x.startswith("INCONCLUSIVE_") for x in states):
        return 2
    return 0


def main():
    results = [probe(*target) for target in TARGETS]
    output = {"read_only": True, "html_reachability_only": True,
              "live_functions_or_deploy_certified": False, "results": results}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if any(x["status"].startswith("INCONCLUSIVE_") for x in results):
        print("::warning::Respuesta de gateway o HTML no concluyente: no se certificó el despliegue")
    if any(x["status"].startswith("ERROR_") for x in results):
        print("::error::Falló la disponibilidad HTTP: revisar publicación y origen")
    return exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
