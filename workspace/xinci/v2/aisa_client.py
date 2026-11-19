import os
import json
import urllib.request
import urllib.error
from v2.budget import Ledger
from v2.util import load_dotenv

QUOTE_URL = "https://tools.aisa.one/v1/tool-router/aisa-batch-quote"
USE_URL = "https://tools.aisa.one/v1/tool-router/aisa-batch-use"

class AisaClient:
  def __init__(self, ledger, timeout=240):
    load_dotenv()
    self.ledger = ledger
    self.timeout = timeout

  def _key(self):
    dry = os.getenv("AISA_DRY_RUN", "").strip() in ("1", "true", "TRUE", "yes")
    key = os.getenv("AISA_API_KEY", "").strip()
    if not key and not dry:
      raise RuntimeError("missing AISA_API_KEY")
    return key

  def _redact(self, text):
    if not text or not isinstance(text, str):
      return text
    key = os.getenv("AISA_API_KEY", "").strip()
    if key and key in text:
      return text.replace(key, "[REDACTED]")
    return text

  def _post(self, url, body, extra_headers=None):
    key = self._key()
    headers = {
      "Content-Type": "application/json",
    }
    if key:
      headers["Authorization"] = f"Bearer {key}"
    if extra_headers:
      headers.update(extra_headers)

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
      with urllib.request.urlopen(req, timeout=self.timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)
    except urllib.error.HTTPError as e:
      err_body = ""
      try:
        err_body = e.read().decode("utf-8")
      except Exception:
        pass
      raise RuntimeError(f"HTTPError {e.code} on {url}: {e.reason} - {self._redact(err_body)}")
    except Exception as e:
      msg = str(e)
      raise RuntimeError(f"Request failed on {url}: {self._redact(msg)}")

  def _fingerprint(self, arguments):
    if arguments is None:
      arguments = {}
    return json.dumps(arguments, sort_keys=True)

  def quote(self, calls):
    dry = os.getenv("AISA_DRY_RUN", "").strip() in ("1", "true", "TRUE", "yes")
    results = {}
    
    if not calls:
      return results

    if dry:
      for c in calls:
        cid = c["call_id"]
        tool = c["tool"]
        args = c.get("arguments", {})
        fp = self._fingerprint(args)
        est_usd = 0.0
        may_exceed = False
        self.ledger.record_quote(tool, cid, est_usd, may_exceed_estimate=may_exceed, note="dry_run")
        results[cid] = {
          "ok": True,
          "estimated_usd": est_usd,
          "may_exceed": may_exceed,
          "fingerprint": fp,
          "tool": tool,
          "arguments": args
        }
      return results

    payload = {
      "calls": [
        {
          "call_id": c["call_id"],
          "tool": c["tool"],
          "arguments": c.get("arguments", {})
        }
        for c in calls
      ]
    }

    resp = self._post(QUOTE_URL, payload)
    resp_results = resp.get("results", [])
    
    # Map calls for quick lookup
    call_map = {c["call_id"]: c for c in calls}

    for r in resp_results:
      cid = r.get("call_id")
      if not cid or cid not in call_map:
        continue
      c = call_map[cid]
      tool = c["tool"]
      args = c.get("arguments", {})
      fp = self._fingerprint(args)

      successful = r.get("successful", False)
      data = r.get("data", {})
      micros = data.get("estimated_cost_micros_usd") if data else None

      if not successful or micros is None:
        self.ledger.skip(tool, cid, reason="quote failed or missing estimate", estimated_usd=None)
        results[cid] = {"ok": False, "estimated_usd": None, "fingerprint": fp, "tool": tool, "arguments": args}
        continue

      est_usd = float(micros) / 1e6
      may_exceed = bool(data.get("may_exceed_estimate", False))

      self.ledger.record_quote(tool, cid, est_usd, may_exceed_estimate=may_exceed)
      results[cid] = {
        "ok": True,
        "estimated_usd": est_usd,
        "may_exceed": may_exceed,
        "fingerprint": fp,
        "tool": tool,
        "arguments": args
      }

    # Handle any calls missing from response
    for c in calls:
      cid = c["call_id"]
      if cid not in results:
        tool = c["tool"]
        args = c.get("arguments", {})
        fp = self._fingerprint(args)
        self.ledger.skip(tool, cid, reason="missing in quote response", estimated_usd=None)
        results[cid] = {"ok": False, "estimated_usd": None, "fingerprint": fp, "tool": tool, "arguments": args}

    return results

  def use(self, calls, quotes):
    dry = os.getenv("AISA_DRY_RUN", "").strip() in ("1", "true", "TRUE", "yes")
    results = {}

    valid_calls = []
    for c in calls:
      cid = c["call_id"]
      tool = c["tool"]
      args = c.get("arguments", {})
      fp = self._fingerprint(args)

      q = quotes.get(cid)
      if not q or not q.get("ok"):
        self.ledger.skip(tool, cid, reason="not quoted or quote not ok")
        results[cid] = {"ok": False, "error": "not quoted"}
        continue

      if q.get("fingerprint") != fp:
        self.ledger.skip(tool, cid, reason="fingerprint mismatch")
        results[cid] = {"ok": False, "error": "fingerprint mismatch"}
        continue

      est_usd = q.get("estimated_usd", 0.0) or 0.0
      if not self.ledger.allows(est_usd):
        self.ledger.skip(tool, cid, reason="budget exceeded", estimated_usd=est_usd)
        results[cid] = {"ok": False, "error": "budget exceeded"}
        continue

      valid_calls.append((c, q))

    if not valid_calls:
      return results

    if dry:
      for c, q in valid_calls:
        cid = c["call_id"]
        tool = c["tool"]
        args = c.get("arguments", {})
        est_usd = q.get("estimated_usd", 0.0)
        
        fixture_path = f"/workspace/xinci/tests/fixtures/aisa/{tool}.json"
        data = {"dry_run": True}
        if os.path.exists(fixture_path):
          try:
            with open(fixture_path, "r", encoding="utf-8") as f:
              data = json.load(f)
          except Exception:
            pass

        actual_usd = 0.0
        self.ledger.record_use(tool, cid, estimated_usd=est_usd, actual_usd=actual_usd, may_exceed_estimate=q.get("may_exceed", False), note="dry_run", status="used")
        results[cid] = {
          "ok": True,
          "actual_usd": actual_usd,
          "data": data
        }
      return results

    total_est = sum(q.get("estimated_usd", 0.0) or 0.0 for _, q in valid_calls)
    max_price_micros = int(round(total_est * 1e6))

    payload = {
      "calls": [
        {
          "call_id": c["call_id"],
          "tool": c["tool"],
          "arguments": c.get("arguments", {})
        }
        for c, _ in valid_calls
      ]
    }

    headers = {
      "X-AISA-Max-Price-USD": str(max_price_micros)
    }

    try:
      resp = self._post(USE_URL, payload, extra_headers=headers)
    except Exception as e:
      for c, q in valid_calls:
        cid = c["call_id"]
        tool = c["tool"]
        est_usd = q.get("estimated_usd", 0.0)
        self.ledger.fail(tool, cid, reason=str(e), estimated_usd=est_usd, actual_usd=None)
        results[cid] = {"ok": False, "error": str(e)}
      return results

    resp_results = resp.get("results", [])
    call_map = {c["call_id"]: (c, q) for c, q in valid_calls}
    responded_cids = set()

    for r in resp_results:
      cid = r.get("call_id")
      if not cid or cid not in call_map:
        continue
      responded_cids.add(cid)
      c, q = call_map[cid]
      tool = c["tool"]
      est_usd = q.get("estimated_usd", 0.0)
      may_exceed = q.get("may_exceed", False)

      successful = r.get("successful", False)
      cust_cost_micros = r.get("customer_cost_micros_usd")
      data = r.get("data", {})

      if not successful:
        err_msg = r.get("error", "execution failed")
        actual_usd = float(cust_cost_micros) / 1e6 if cust_cost_micros is not None else None
        self.ledger.fail(tool, cid, reason=err_msg, estimated_usd=est_usd, actual_usd=actual_usd)
        results[cid] = {"ok": False, "error": err_msg, "data": data}
        continue

      actual_usd = float(cust_cost_micros) / 1e6 if cust_cost_micros is not None else None
      self.ledger.record_use(tool, cid, estimated_usd=est_usd, actual_usd=actual_usd, may_exceed_estimate=may_exceed, note="", status="used")
      results[cid] = {
        "ok": True,
        "actual_usd": actual_usd,
        "data": data
      }

    for cid, (c, q) in call_map.items():
      if cid not in responded_cids:
        tool = c["tool"]
        est_usd = q.get("estimated_usd", 0.0)
        self.ledger.fail(tool, cid, reason="missing in use response", estimated_usd=est_usd, actual_usd=None)
        results[cid] = {"ok": False, "error": "missing in use response"}

    return results

  def quote_and_use(self, calls):
    quotes = self.quote(calls)
    return self.use(calls, quotes)
