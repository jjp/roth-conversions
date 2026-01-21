from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PINNED_DIR = ROOT / "roth_conversions" / "data" / "tax"
SOURCES_DIR = ROOT / "data" / "irs_sources"


DEFAULT_NEWSROOM_URLS: dict[int, str] = {
    2024: "https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2024",
    2025: "https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2025",
    2026: "https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill",
}


def _download_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "retirement-toolkit/0.1 (+https://github.com/)"})
    with urllib.request.urlopen(req) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _download_file(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "retirement-toolkit/0.1 (+https://github.com/)"})
    with urllib.request.urlopen(req) as resp:
        out_path.write_bytes(resp.read())


def _parse_money_int(s: str) -> int:
    return int(s.replace(",", "").replace("$", "").strip())


def _extract_standard_deduction(text: str, tax_year: int) -> tuple[int, int]:
    # Try both common newsroom phrasings.
    mfj_patterns = (
        rf"standard deduction[^.]*?tax year {tax_year}[^.]*?\$(\d[\d,]*)[^.]*?married couples filing jointly",
        rf"married couples filing jointly[^.]*?standard deduction[^.]*?(?:rises|increases) to \$(\d[\d,]*)",
        rf"standard deduction[^.]*?(?:rises|increases) to \$(\d[\d,]*)[^.]*?married couples filing jointly",
    )
    single_patterns = (
        rf"single taxpayers[^.]*?standard deduction[^.]*?(?:rises|increases) to \$(\d[\d,]*)",
        rf"standard deduction[^.]*?(?:rises|increases) to \$(\d[\d,]*)[^.]*?single taxpayers",
    )

    m_mfj = None
    for pat in mfj_patterns:
        m_mfj = re.search(pat, text, re.IGNORECASE)
        if m_mfj:
            break

    m_single = None
    for pat in single_patterns:
        m_single = re.search(pat, text, re.IGNORECASE)
        if m_single:
            break

    if not m_mfj or not m_single:
        raise ValueError("Could not parse standard deduction values from newsroom text")

    return _parse_money_int(m_mfj.group(1)), _parse_money_int(m_single.group(1))


def extract_from_newsroom(*, html_or_text: str, tax_year: int) -> dict:
    """Extract bracket thresholds + standard deduction from an IRS newsroom page.

    This is intentionally conservative (regex-based) and meant as a helper, not a runtime dependency.
    If the IRS page formatting changes, you can always update the pinned JSON manually.
    """

    year = int(tax_year)
    text = re.sub(r"\s+", " ", html_or_text)

    sd_mfj, sd_single = _extract_standard_deduction(text, year)

    # 37% threshold line
    m_top = re.search(
        r"top tax rate remains 37% .*? single taxpayers.*? greater than \$(\d[\d,]*) \(\$(\d[\d,]*) for married couples filing jointly\)",
        text,
        re.IGNORECASE,
    )
    if not m_top:
        raise ValueError("Could not parse 37% thresholds")

    single_37 = _parse_money_int(m_top.group(1))
    mfj_37 = _parse_money_int(m_top.group(2))

    # Other rates (12/22/24/32/35) are typically described as "X% for incomes over $A ($B for MFJ)"
    pairs = re.findall(
        r"(\d{2})% for incomes over \$(\d[\d,]*) \(\$(\d[\d,]*) for married couples filing jointly\)",
        text,
        flags=re.IGNORECASE,
    )
    starts_single: dict[int, int] = {}
    starts_mfj: dict[int, int] = {}
    for rate_s, single_s, mfj_s in pairs:
        r = int(rate_s)
        starts_single[r] = _parse_money_int(single_s)
        starts_mfj[r] = _parse_money_int(mfj_s)

    # 10% ceiling is described in a couple of ways.
    m_10 = re.search(
        r"lowest rate is 10% .*? incomes of single .*? incomes of \$(\d[\d,]*)\s*or less \(\$(\d[\d,]*) for married couples filing jointly\)",
        text,
        re.IGNORECASE,
    )
    if not m_10:
        m_10 = re.search(
            r"10% for incomes[^$]*\$(\d[\d,]*)\s*or less\s*\(\$(\d[\d,]*)\s*or less for married couples filing jointly\)",
            text,
            re.IGNORECASE,
        )
    if not m_10:
        raise ValueError("Could not parse 10% ceilings")

    single_10 = _parse_money_int(m_10.group(1))
    mfj_10 = _parse_money_int(m_10.group(2))

    # Derive bracket ceilings from bracket starts.
    # We need starts for 12/22/24/32/35. If 12 isn't present (unlikely), fall back to 10% ceiling.
    def build(ten_ceiling: int, starts: dict[int, int], top_start: int) -> list[dict]:
        start_12 = starts.get(12, ten_ceiling)
        required = (22, 24, 32, 35)
        missing = [r for r in required if r not in starts]
        if missing:
            raise ValueError(f"Missing bracket thresholds for rates: {missing}")
        return [
            {"ceiling": ten_ceiling, "rate": 0.10},
            {"ceiling": starts[22], "rate": 0.12},
            {"ceiling": starts[24], "rate": 0.22},
            {"ceiling": starts[32], "rate": 0.24},
            {"ceiling": starts[35], "rate": 0.32},
            {"ceiling": top_start, "rate": 0.35},
            {"ceiling": None, "rate": 0.37},
        ]

    mfj = build(mfj_10, starts_mfj, mfj_37)
    single = build(single_10, starts_single, single_37)

    return {
        "metadata": {
            "source": {
                "title": f"IRS newsroom (tax year {year})",
                "url": DEFAULT_NEWSROOM_URLS.get(year, ""),
            },
            "notes": "Generated by scripts/update_irs_tax_tables.py; review before committing.",
        },
        "tax_year": year,
        "ordinary_income": {
            "brackets": {"MFJ": mfj, "Single": single},
            "standard_deduction": {"MFJ": sd_mfj, "Single": sd_single},
        },
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Update pinned IRS tax tables (helper script)")
    p.add_argument("--tax-year", type=int, default=2024, help="Tax year to update (currently supports 2024)")
    p.add_argument(
        "--news-url",
        default=None,
        help="Override IRS newsroom URL (defaults are built in for supported years)",
    )
    p.add_argument(
        "--rev-proc-url",
        default=None,
        help="Optional Rev. Proc PDF URL to download into data/irs_sources/",
    )
    args = p.parse_args(argv)

    tax_year = int(args.tax_year)

    if args.rev_proc_url:
        SOURCES_DIR.mkdir(parents=True, exist_ok=True)
        name = Path(args.rev_proc_url).name
        out = SOURCES_DIR / name
        print(f"Downloading Rev. Proc PDF -> {out}")
        _download_file(str(args.rev_proc_url), out)

    news_url = str(args.news_url or DEFAULT_NEWSROOM_URLS.get(tax_year) or "")
    if not news_url:
        raise SystemExit(f"No default newsroom URL for tax_year={tax_year}. Provide --news-url.")

    print(f"Fetching newsroom page: {news_url}")
    page = _download_text(news_url)

    table = extract_from_newsroom(html_or_text=page, tax_year=tax_year)

    PINNED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PINNED_DIR / f"us_federal_ordinary_income_{tax_year}.json"
    out_path.write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote pinned tax table: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
