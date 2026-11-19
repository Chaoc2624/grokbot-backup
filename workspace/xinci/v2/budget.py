import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path


def usd_from_micros(n: int) -> float:
    return float(n) / 1_000_000.0


class Ledger:
    def __init__(self, path=None, date=None, hard_cap_usd=1.0, today_prior_usd=0.0):
        if path is None:
            self.path = Path(__file__).resolve().parents[1] / "v2_spend.json"
        else:
            self.path = Path(path)

        tz = timezone(timedelta(hours=8))
        if date is None:
            self.date = datetime.now(tz).strftime("%Y-%m-%d")
        else:
            self.date = date

        self.hard_cap_usd = float(hard_cap_usd)
        self.today_prior_usd = float(today_prior_usd)
        self.entries = []

        self._load_and_normalize()

    def _now_str(self):
        tz = timezone(timedelta(hours=8))
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    def _load_and_normalize(self):
        if not self.path.exists():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        stored_date = data.get("date")
        if stored_date == self.date:
            self.hard_cap_usd = float(data.get("hard_cap_usd", self.hard_cap_usd))
            self.today_prior_usd = float(data.get("today_prior_usd", self.today_prior_usd))
            self.entries = data.get("entries", [])
        else:
            # If different date, we start fresh for today. 
            # We don't mix other dates into remaining.
            pass

    @property
    def actual_usd(self) -> float:
        total = 0.0
        for entry in self.entries:
            # actuals from used or failed-after-use entries if actual_usd is not None
            if entry.get("status") in ("used", "failed") and entry.get("actual_usd") is not None:
                total += float(entry["actual_usd"])
        return total

    @property
    def estimated_usd(self) -> float:
        total = 0.0
        for entry in self.entries:
            if entry.get("status") in ("used", "failed", "quoted"):
                est = entry.get("estimated_usd")
                if est is not None:
                    total += float(est)
        return total

    @property
    def accounted_this_run(self) -> float:
        total = 0.0
        for entry in self.entries:
            status = entry.get("status")
            # accounted for each used/failed-after-use entry: 
            # add actual if not None else estimated
            if status in ("used", "failed"):
                actual = entry.get("actual_usd")
                if actual is not None:
                    total += float(actual)
                else:
                    est = entry.get("estimated_usd")
                    if est is not None:
                        total += float(est)
        return total

    @property
    def remaining_usd(self) -> float:
        return self.hard_cap_usd - self.today_prior_usd - self.accounted_this_run

    def allows(self, est_usd, reserve_usd=0) -> bool:
        if est_usd is None:
            return False
        return (self.remaining_usd - float(reserve_usd)) >= float(est_usd)

    def _add_entry(self, tool, call_id, estimated_usd, actual_usd, may_exceed_estimate, note, status):
        actual_unknown = False
        if status in ("used", "failed"):
            if actual_usd is None:
                actual_unknown = True

        entry = {
            "at": self._now_str(),
            "tool": str(tool),
            "call_id": str(call_id),
            "estimated_usd": float(estimated_usd) if estimated_usd is not None else None,
            "actual_usd": float(actual_usd) if actual_usd is not None else None,
            "may_exceed_estimate": bool(may_exceed_estimate),
            "status": str(status),
            "note": str(note),
            "actual_unknown": bool(actual_unknown)
        }
        self.entries.append(entry)
        self.save()

    def record_quote(self, tool, call_id, estimated_usd, may_exceed_estimate=False, note=""):
        self._add_entry(tool, call_id, estimated_usd, None, may_exceed_estimate, note, "quoted")

    def record_use(self, tool, call_id, estimated_usd, actual_usd, may_exceed_estimate=False, note="", status="used"):
        self._add_entry(tool, call_id, estimated_usd, actual_usd, may_exceed_estimate, note, status)

    def skip(self, tool, call_id, reason, estimated_usd=None):
        self._add_entry(tool, call_id, estimated_usd, None, False, reason, "skipped")

    def fail(self, tool, call_id, reason, estimated_usd=None, actual_usd=None):
        self._add_entry(tool, call_id, estimated_usd, actual_usd, False, reason, "failed")

    def as_dict(self) -> dict:
        return {
            "date": self.date,
            "hard_cap_usd": self.hard_cap_usd,
            "today_prior_usd": self.today_prior_usd,
            "actual_usd": self.actual_usd,
            "estimated_usd": self.estimated_usd,
            "remaining_usd": self.remaining_usd,
            "entries": self.entries
        }

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = self.as_dict()
        
        # Atomic write (tmp + replace)
        fd, tmp_path = tempfile.mkstemp(dir=self.path.parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / "v2_spend.json"
        print(f"Demo Ledger path: {tmp_file}")

        ledger = Ledger(path=tmp_file, hard_cap_usd=2.0)
        print(f"Initial remaining: {ledger.remaining_usd}")

        est = usd_from_micros(150000) # $0.15
        if ledger.allows(est):
            print("Budget allows 150k micros. Recording quote...")
            ledger.record_quote("search_tool", "call_123", estimated_usd=est, note="Initial search")
        
        print(f"Remaining after quote: {ledger.remaining_usd}")

        act = usd_from_micros(120000) # $0.12 actual
        ledger.record_use("search_tool", "call_123", estimated_usd=est, actual_usd=act, note="Completed successfully")
        
        print(f"Remaining after use: {ledger.remaining_usd}")
        print(f"Actual USD: {ledger.actual_usd}")
        print("Ledger dict:", json.dumps(ledger.as_dict(), indent=2))
