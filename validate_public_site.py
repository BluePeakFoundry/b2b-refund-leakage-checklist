#!/usr/bin/env python3
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
CANONICAL = "https://bluepeakfoundry.github.io/b2b-refund-leakage-checklist/"
FEEDBACK_URL = "https://github.com/BluePeakFoundry/b2b-refund-leakage-checklist/issues/new?template=feedback.yml"
REVIEW_REQUEST_URL = "https://github.com/BluePeakFoundry/b2b-refund-leakage-checklist/issues/new?template=review-request.yml"
REQUIRED_LINKS = {
    FEEDBACK_URL,
    REVIEW_REQUEST_URL,
    "https://bluepeakfoundry.github.io/consumer-rights-tools/",
    "downloads/refund-leakage-review.csv",
    "downloads/vendor-message-template.md",
    "downloads/ap-duplicate-invoice-checks.sql",
    "downloads/ap-sql-starter-guide.md",
}
PROHIBITED_TERMS = [
    r"\bsergi\b",
    r"\brex\b",
    r"\bagent\b",
    r"\bbot\b",
    r"\bautonomous\b",
    r"\bcycle\b",
    r"money verified",
    r"monetization matrix",
    r"guaranteed refund",
    r"guaranteed savings",
]
REMOTE_RUNTIME_RE = re.compile(
    r"<(script|img|iframe|source|video|audio)\b[^>]*src=[\"']https?://|"
    r"<link\b(?=[^>]*rel=[\"'](?:stylesheet|preload|modulepreload|icon)[\"'])[^>]*href=[\"']https?://",
    re.I,
)
FORM_OR_TRACKING_RE = re.compile(r"<form\b|google-analytics|googletagmanager|plausible\.io|gtag\(|dataLayer", re.I)

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()
        self.canonical = None
        self.stylesheets = []
        self.json_ld = []
        self.ids = set()
        self.skip_links = []
        self._in_json_ld = False

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if "id" in data:
            self.ids.add(data["id"])
        if tag == "a" and data.get("href"):
            self.links.add(data["href"])
            if data.get("class") == "skip-link":
                self.skip_links.append(data["href"])
        if tag == "link" and data.get("rel") == "canonical":
            self.canonical = data.get("href")
        if tag == "link" and data.get("rel") == "stylesheet":
            self.stylesheets.append(data.get("href"))
        self._in_json_ld = tag == "script" and data.get("type") == "application/ld+json"

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_json_ld = False

    def handle_data(self, data):
        if self._in_json_ld:
            self.json_ld.append(data)


def fail(message):
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_html():
    text = (ROOT / "index.html").read_text(encoding="utf-8")
    lowered = text.lower()
    for term in PROHIBITED_TERMS:
        if re.search(term, lowered):
            fail(f"prohibited public language: {term}")
    remote_runtime_text = re.sub(r"<script[^>]+src=['\"]https://gc\.zgo\.at/count\.js['\"][^>]*></script>", "", text, flags=re.I)
    if REMOTE_RUNTIME_RE.search(remote_runtime_text):
        fail("remote runtime resource detected")
    if FORM_OR_TRACKING_RE.search(text):
        fail("forbidden form or invasive tracking marker detected")
    for marker in ["bluepeakfoundry.goatcounter.com/count", "analytics.js", "data-analytics-event", "data-analytics-event=\"lead\""]:
        if marker not in text:
            fail(f"missing analytics marker: {marker}")
    parser = Parser()
    parser.feed(text)
    if parser.canonical != CANONICAL:
        fail(f"canonical mismatch: {parser.canonical}")
    missing = REQUIRED_LINKS - parser.links
    if missing:
        fail(f"missing required links: {sorted(missing)}")
    if parser.stylesheets != ["style.css"]:
        fail(f"unexpected stylesheet refs: {parser.stylesheets}")
    if "#checklist" not in parser.skip_links or "checklist" not in parser.ids:
        fail("skip link target missing")
    raw_json = "".join(parser.json_ld).strip()
    if not raw_json:
        fail("missing JSON-LD")
    payload = json.loads(raw_json)
    graph = payload.get("@graph", [])
    types = {entry.get("@type") for entry in graph if isinstance(entry, dict)}
    if not {"WebSite", "HowTo", "FAQPage"}.issubset(types):
        fail(f"missing JSON-LD types: {types}")
    if "No refund, saving, recovery, or outcome is guaranteed." not in text:
        fail("missing outcome disclaimer")


def validate_robots_sitemap():
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if "Allow: /" not in robots or f"Sitemap: {CANONICAL}sitemap.xml" not in robots:
        fail("robots.txt missing allow or sitemap")
    tree = ET.parse(ROOT / "sitemap.xml")
    locs = {node.text for node in tree.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}
    if CANONICAL not in locs:
        fail("sitemap missing canonical URL")


def validate_feedback_template():
    path = ROOT / ".github" / "ISSUE_TEMPLATE" / "feedback.yml"
    if not path.exists():
        fail("missing feedback issue template")
    text = path.read_text(encoding="utf-8")
    required_phrases = [
        "No confidential data",
        "No personal data",
        "No client names",
        "No vendor names",
        "No invoice numbers",
        "No account IDs",
        "No contract text",
    ]
    lowered = text.lower()
    missing = [phrase for phrase in required_phrases if phrase.lower() not in lowered]
    if missing:
        fail(f"feedback template missing safety phrases: {missing}")
    if "contact_links" in lowered:
        fail("feedback template must not add external contact links")


def validate_review_request_template():
    path = ROOT / ".github" / "ISSUE_TEMPLATE" / "review-request.yml"
    if not path.exists():
        fail("missing review request issue template")
    text = path.read_text(encoding="utf-8")
    required_phrases = [
        "No confidential data",
        "No personal data",
        "No client names",
        "No vendor names",
        "No invoice numbers",
        "No account numbers",
        "No account IDs",
        "No pricing terms",
        "No contract terms",
        "No contract text",
        "No guaranteed response",
        "No guaranteed refund",
    ]
    lowered = text.lower()
    missing = [phrase for phrase in required_phrases if phrase.lower() not in lowered]
    if missing:
        fail(f"review request template missing safety phrases: {missing}")
    if "contact_links" in lowered:
        fail("review request template must not add external contact links")


def validate_downloads():
    csv_path = ROOT / "downloads" / "refund-leakage-review.csv"
    template_path = ROOT / "downloads" / "vendor-message-template.md"
    sql_path = ROOT / "downloads" / "ap-duplicate-invoice-checks.sql"
    guide_path = ROOT / "downloads" / "ap-sql-starter-guide.md"
    if not csv_path.exists() or not template_path.exists() or not sql_path.exists() or not guide_path.exists():
        fail("missing downloadable helper files")
    csv_text = csv_path.read_text(encoding="utf-8")
    if "avoid_sharing_publicly" not in csv_text or "invoice numbers" not in csv_text:
        fail("CSV helper missing privacy guidance")
    template_text = template_path.read_text(encoding="utf-8")
    required = ["Billing review request", "safest official channel", "Do not post confidential data"]
    missing = [phrase for phrase in required if phrase not in template_text]
    if missing:
        fail(f"vendor template missing phrases: {missing}")
    sql_text = sql_path.read_text(encoding="utf-8")
    guide_text = guide_path.read_text(encoding="utf-8")
    for phrase in ["Do not upload or paste live bank details", "review_query", "duplicate invoice"]:
        if phrase.lower() not in sql_text.lower():
            fail(f"SQL starter missing phrase: {phrase}")
    for phrase in ["Do not use live bank details", "review lead", "No refund, saving, recovery"]:
        if phrase.lower() not in guide_text.lower():
            fail(f"SQL guide missing phrase: {phrase}")


def validate_manifest():
    data = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    if data.get("money_verified_eur") != 0:
        fail("manifest money_verified_eur must be 0")
    if data.get("external_actions_performed") != []:
        fail("manifest external_actions_performed must be empty before publish")
    if data.get("public_url") != CANONICAL:
        fail("manifest public_url mismatch")
    files = {entry["path"]: entry for entry in data.get("files", [])}
    required = {
        "index.html",
        "style.css",
        "robots.txt",
        "sitemap.xml",
        "README.md",
        "validate_public_site.py",
        "manifest.json",
        ".github/ISSUE_TEMPLATE/feedback.yml",
        ".github/ISSUE_TEMPLATE/review-request.yml",
        ".github/workflows/traffic-snapshot.yml",
        "analytics.js",
        "downloads/refund-leakage-review.csv",
        "downloads/vendor-message-template.md",
        "downloads/ap-duplicate-invoice-checks.sql",
        "downloads/ap-sql-starter-guide.md",
    }
    if not required.issubset(files):
        fail(f"manifest missing files: {sorted(required - set(files))}")
    for rel, entry in files.items():
        path = ROOT / rel
        if path.exists() and rel != "manifest.json" and entry.get("sha256") != sha256(path):
            fail(f"manifest hash mismatch: {rel}")


def main():
    validate_html()
    validate_robots_sitemap()
    validate_feedback_template()
    validate_review_request_template()
    validate_downloads()
    validate_manifest()
    data = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    print(f"OK b2b refund leakage checklist files={len(data.get('files', []))} money_verified_eur={data['money_verified_eur']} external_actions={len(data['external_actions_performed'])}")

if __name__ == "__main__":
    main()
