"""
Автоматизированный сбор формального институционального слоя с официальных сайтов.

Что делает модуль:
1. Пытается в live-режиме получить данные с официальных страниц:
   - Кремль
   - Правительство РФ
   - Государственная Дума
   - Совет Федерации
2. Если live-сбор недоступен (например, офлайн-проверка, блокировки, отсутствие DNS),
   загружает кэшированный snapshot из репозитория.
3. Возвращает единую таблицу официального институционального слоя, которую можно
   использовать в анализе и показать на защите как отдельный этап data collection.

Важно:
- Кэшированный snapshot включен специально для воспроизводимости проекта без интернета.
- Итоговый проект остается кодовым: сбор, нормализация, объединение и визуализация
  выполняются Python-кодом.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = BASE_DIR / "data" / "raw" / "official_collection"
CACHE_FILE = CACHE_DIR / "official_snapshot_cache.csv"


@dataclass
class Provider:
    name: str
    url: str
    parser: Callable[[str], list[dict]]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _safe_get(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    return response.text


def _rows_to_df(rows: list[dict], provider: str) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(
            columns=[
                "provider", "entity_group", "institution_id", "institution_name",
                "position_id", "position_name", "person_id", "person_name",
                "source_url", "source_type", "snapshot_date", "collection_mode", "notes"
            ]
        )
    df = pd.DataFrame(rows)
    df["provider"] = provider
    df["source_type"] = "official_site"
    df["snapshot_date"] = pd.Timestamp.today().date().isoformat()
    df["collection_mode"] = "live_scrape"
    return df


def parse_government_persons(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    rows = []
    anchors = soup.select("a[href*='/gov/persons/']")
    for a in anchors:
        text = _clean(a.get_text(" ", strip=True))
        href = a.get("href") or ""
        if not text or text.startswith("/"):
            continue
        rows.append({
            "entity_group": "person",
            "institution_id": "org_government_rf",
            "institution_name": "Правительство Российской Федерации",
            "position_id": "",
            "position_name": "",
            "person_id": "",
            "person_name": text,
            "source_url": href if href.startswith("http") else f"https://government.ru{href}",
            "notes": "Собрано автоматически со страницы персон Правительства РФ."
        })
    return rows


def parse_kremlin_admin(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    rows = []
    anchors = soup.select("a[href*='/catalog/persons/'], a[href*='/structure/administration/members/']")
    for a in anchors:
        text = _clean(a.get_text(" ", strip=True))
        href = a.get("href") or ""
        if not text or len(text) < 5:
            continue
        rows.append({
            "entity_group": "person",
            "institution_id": "org_ap_rf",
            "institution_name": "Администрация Президента Российской Федерации",
            "position_id": "",
            "position_name": "",
            "person_id": "",
            "person_name": text,
            "source_url": href if href.startswith("http") else f"https://www.kremlin.ru{href}",
            "notes": "Собрано автоматически со страницы членов Администрации Президента."
        })
    return rows


def parse_duma_chair(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    rows = []
    title = _clean(soup.title.get_text(" ", strip=True)) if soup.title else ""
    candidate = title.replace("Председатель Государственной Думы", "").strip(" -–|")
    if candidate:
        rows.append({
            "entity_group": "person",
            "institution_id": "org_state_duma",
            "institution_name": "Государственная Дума Федерального Собрания Российской Федерации",
            "position_id": "pos_chair_state_duma",
            "position_name": "Председатель Государственной Думы Федерального Собрания Российской Федерации",
            "person_id": "",
            "person_name": candidate,
            "source_url": "https://duma.gov.ru/duma/chairman/",
            "notes": "Собрано автоматически со страницы председателя Государственной Думы."
        })
    return rows


def parse_council_chair(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    rows = []
    page_text = _clean(soup.get_text(" ", strip=True))
    # Консервативный паттерн, потому что страница может меняться.
    m = re.search(r"Валентина\s+Матвиенко|Матвиенко\s+Валентина", page_text, flags=re.I)
    if m:
        rows.append({
            "entity_group": "person",
            "institution_id": "org_federation_council",
            "institution_name": "Совет Федерации Федерального Собрания Российской Федерации",
            "position_id": "pos_chair_federation_council",
            "position_name": "Председатель Совета Федерации Федерального Собрания Российской Федерации",
            "person_id": "",
            "person_name": "Валентина Матвиенко",
            "source_url": "https://www.council.gov.ru/structure/persons/257/",
            "notes": "Собрано автоматически со страницы председателя Совета Федерации."
        })
    return rows


PROVIDERS = [
    Provider("government", "https://government.ru/gov/persons/", parse_government_persons),
    Provider("kremlin", "https://www.kremlin.ru/structure/administration/members", parse_kremlin_admin),
    Provider("duma", "https://duma.gov.ru/duma/chairman/", parse_duma_chair),
    Provider("council", "https://www.council.gov.ru/structure/persons/257/", parse_council_chair),
]


def scrape_live_snapshot() -> pd.DataFrame:
    parts = []
    for provider in PROVIDERS:
        html = _safe_get(provider.url)
        rows = provider.parser(html)
        parts.append(_rows_to_df(rows, provider.name))
    if not parts:
        raise RuntimeError("No live providers returned data")
    df = pd.concat(parts, ignore_index=True, sort=False)
    if df.empty:
        raise RuntimeError("Live official collection returned empty dataframe")
    return df.drop_duplicates()


def load_cached_snapshot() -> pd.DataFrame:
    if not CACHE_FILE.exists():
        raise FileNotFoundError(f"Cached official snapshot not found: {CACHE_FILE}")
    df = pd.read_csv(CACHE_FILE)
    return df


def collect_official_snapshot(prefer_live: bool = True, save_processed: bool = False) -> pd.DataFrame:
    if prefer_live:
        try:
            df = scrape_live_snapshot()
        except Exception:
            df = load_cached_snapshot()
    else:
        df = load_cached_snapshot()

    if save_processed:
        out_dir = BASE_DIR / "data" / "processed"
        out_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_dir / "official_snapshot.csv", index=False)
    return df


if __name__ == "__main__":
    df = collect_official_snapshot(prefer_live=True, save_processed=True)
    print(df.head())
    print("official snapshot rows:", len(df))
