#!/usr/bin/env python3
"""Elden Console - coleta de dados.

Puxa os numeros do GitHub via GraphQL: uma query de perfil (seguidores, PRs,
stars, linguagens) e uma query multi-alias por ano para o historico all-time
(contributionsCollection cobre no maximo 1 ano por request).

Regra de ouro: nunca comeca do zero. Carrega o JSON anterior e so sobrescreve
o que conseguiu buscar - assim uma API fora do ar nao zera o perfil.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

from theme import DATA

LOGIN = os.environ.get("PROFILE_LOGIN", "lucasmoura333")
API = "https://api.github.com/graphql"


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def resolve_token() -> str:
    token = os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except Exception as ex:  # noqa: BLE001
        raise SystemExit(f"error: sem token do GitHub ({ex})")


def http_json(url: str, headers: dict[str, str], body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as ex:  # noqa: PERF203
        detail = ex.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {ex.code}: {detail[:300]}") from ex


def graphql(token: str, query: str, variables: dict | None = None) -> dict:
    res = http_json(
        API,
        headers={
            "Authorization": f"bearer {token}",
            "User-Agent": "elden-console",
            "Content-Type": "application/json",
        },
        body={"query": query, "variables": variables or {}},
    )
    if res.get("errors"):
        raise RuntimeError("GraphQL: " + "; ".join(e["message"] for e in res["errors"]))
    return res["data"]


PROFILE_QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    merged: pullRequests(states: MERGED) { totalCount }
    contributionsCollection { contributionYears }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        name
        url
        stargazerCount
        forkCount
        languages(first: 20) { edges { size node { name } } }
      }
    }
  }
}
"""


def years_query(years: list[int]) -> str:
    parts = []
    for y in years:
        parts.append(
            """
    y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") {{
      contributionCalendar {{
        totalContributions
        weeks {{ contributionDays {{ date contributionCount }} }}
      }}
    }}""".format(y=y)
        )
    return "query($login: String!) {\n  user(login: $login) {" + "".join(parts) + "\n  }\n}"


def fetch_github(token: str) -> tuple[dict, dict]:
    data = graphql(token, PROFILE_QUERY, {"login": LOGIN})["user"]
    years = sorted(data["contributionsCollection"]["contributionYears"])

    cal = graphql(token, years_query(years), {"login": LOGIN})["user"]

    days: dict[str, int] = {}
    all_time = 0
    year_totals: dict[int, int] = {}
    for y in years:
        block = cal.get(f"y{y}") or {}
        calendar_block = block.get("contributionCalendar") or {}
        all_time += calendar_block.get("totalContributions", 0)
        year_totals[y] = calendar_block.get("totalContributions", 0)
        for week in calendar_block.get("weeks", []):
            for day in week.get("contributionDays", []):
                days[day["date"]] = day["contributionCount"]

    today = datetime.now(timezone.utc).date()
    current, longest = streaks(days, today)

    repos = data["repositories"]["nodes"]
    stars = sum(r["stargazerCount"] for r in repos)
    forks = sum(r["forkCount"] for r in repos)

    lang_bytes: dict[str, int] = {}
    for r in repos:
        for edge in r["languages"]["edges"]:
            lang_bytes[edge["node"]["name"]] = lang_bytes.get(edge["node"]["name"], 0) + edge["size"]
    total_bytes = sum(lang_bytes.values()) or 1
    languages = [
        {"name": n, "bytes": b, "percent": round(100 * b / total_bytes, 1)}
        for n, b in sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)
    ]

    stats = {
        "login": LOGIN,
        "name": data.get("name") or LOGIN,
        "member_since": data["createdAt"][:10],
        "followers": data["followers"]["totalCount"],
        "public_repos": data["repositories"]["totalCount"],
        "total_stars": stars,
        "total_forks": forks,
        "pull_requests": data["pullRequests"]["totalCount"],
        "merged_prs": data["merged"]["totalCount"],
        "contributions_all_time": all_time,
        "contributions_year": year_totals.get(today.year, 0),
        "current_streak": current,
        "longest_streak": longest,
        "languages": languages,
        "repos": [
            {"name": r["name"], "url": r["url"], "stars": r["stargazerCount"], "forks": r["forkCount"]}
            for r in sorted(repos, key=lambda r: r["stargazerCount"], reverse=True)
        ],
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    grid = build_grid(days, today)
    calendar = {
        "generated_at": stats["fetched_at"],
        "today": today.isoformat(),
        "days": days,
        "grid": grid,
    }
    return stats, calendar


def build_grid(days: dict[str, int], today: date) -> list[list[dict]]:
    """Ultimas 53 semanas (domingo->sabado), igual ao grafico do GitHub."""
    end = today + timedelta(days=(6 - today.weekday()) % 7)
    start = end - timedelta(days=53 * 7 - 1)
    weeks = []
    cursor = start
    while cursor <= end:
        week = []
        for _ in range(7):
            key = cursor.isoformat()
            week.append({"date": key, "count": days.get(key, 0), "future": cursor > today})
            cursor += timedelta(days=1)
        weeks.append(week)
    return weeks


def streaks(days: dict[str, int], today: date) -> tuple[int, int]:
    longest = run = 0
    for d in sorted(k for k in days if k <= today.isoformat()):
        run = run + 1 if days[d] > 0 else 0
        longest = max(longest, run)

    current, d = 0, today
    if days.get(d.isoformat(), 0) == 0:
        d -= timedelta(days=1)
    while days.get(d.isoformat(), 0) > 0:
        current += 1
        d -= timedelta(days=1)
    return current, longest


def load(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:  # noqa: BLE001
        return default


def save(path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    stats = load(DATA / "stats.json", {})
    calendar = load(DATA / "calendar.json", {})

    try:
        new_stats, new_calendar = fetch_github(resolve_token())
        stats.update(new_stats)
        calendar = new_calendar
    except Exception as ex:  # noqa: BLE001
        warn(f"GitHub fetch falhou, mantendo dados anteriores: {ex}")
        if not stats:
            return 1

    save(DATA / "stats.json", stats)
    save(DATA / "calendar.json", calendar)
    print(
        f"ok: {stats.get('contributions_all_time')} contribuicoes all-time, "
        f"{stats.get('current_streak')}d streak atual, {len(stats.get('repos', []))} repos"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
