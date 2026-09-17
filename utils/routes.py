"""The routing table behind the capability tools.

Each capability tool (people_search, company_intelligence, seo_research,
web_research, social_research) takes an `action` and a `provider`. This
module says which Glasser endpoint serves each (action, provider) pair and
how the tool's flat parameters become that endpoint's provider-native
input. `provider = auto` picks the entry named in AUTO.

Every endpoint here was inspected on 2026-09-17; the builders follow the
input_schema each inspect returned. When a provider changes its contract,
Glasser bumps the endpoint_version and this table is where the plugin
follows.
"""

import datetime as _dt
from dataclasses import dataclass
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from utils import geo


class InvalidInput(Exception):
    """A parameter the route cannot use. Raised before any API call."""


@dataclass(frozen=True)
class Route:
    provider: str
    endpoint: str
    endpoint_version: int
    build: Callable[[dict[str, Any]], dict[str, Any]]
    note: str = ""


# ------------------------------------------------------------- helpers


def _s(p: dict[str, Any], key: str) -> Optional[str]:
    value = p.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _list(p: dict[str, Any], key: str) -> list[str]:
    raw = p.get(key)
    if raw is None:
        return []
    if isinstance(raw, list):
        items = [str(x).strip() for x in raw]
    else:
        items = [x.strip() for x in str(raw).split(",")]
    return [x for x in items if x]


def _int(p: dict[str, Any], key: str, default: int, lo: int = 1, hi: int = 100) -> int:
    raw = p.get(key)
    if raw is None or raw == "":
        return default
    try:
        n = int(float(raw))
    except (TypeError, ValueError):
        raise InvalidInput(f"'{key}' must be an integer.")
    return max(lo, min(hi, n))


def _need(p: dict[str, Any], key: str, why: str = "") -> str:
    value = _s(p, key)
    if value is None:
        raise InvalidInput(f"'{key}' is required{(' ' + why) if why else ''}.")
    return value


def _domain(p: dict[str, Any], key: str = "domain") -> str:
    raw = _need(p, key)
    host = raw
    if "://" in raw:
        host = urlparse(raw).netloc or raw
    host = host.split("/")[0].strip().lower()
    if host.startswith("www."):
        host = host[4:]
    if "." not in host:
        raise InvalidInput(f"'{key}' must be a domain such as stripe.com, got '{raw}'.")
    return host


def _linkedin_handle(url: str) -> str:
    path = urlparse(url if "://" in url else "https://" + url).path
    parts = [x for x in path.split("/") if x]
    if len(parts) >= 2 and parts[0] == "in":
        return parts[1]
    return parts[-1] if parts else url


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split()
    if len(parts) < 2:
        raise InvalidInput("'full_name' needs a first and a last name.")
    return parts[0], " ".join(parts[1:])


def _month_start() -> str:
    """Ahrefs wants a date; the first of the current month is always in the index."""
    today = _dt.date.today()
    return today.replace(day=1).isoformat()


def _clean(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None and v != "" and v != []}


# ------------------------------------------------------------ people_search


def _people_search_apollo(p):
    titles, locs, domain = _list(p, "job_titles"), _list(p, "locations"), _s(p, "company_domain")
    keywords = _s(p, "keywords")
    if not (titles or locs or domain or keywords):
        raise InvalidInput("people_search needs at least one of job_titles, locations, company_domain, keywords.")
    return _clean({
        "per_page": _int(p, "limit", 5, 1, 25),
        "person_titles[]": titles,
        "person_locations[]": locs,
        "person_seniorities[]": _list(p, "seniorities"),
        "q_organization_domains_list[]": [_domain(p, "company_domain")] if domain else [],
        "q_keywords": keywords,
    })


def _people_search_pdl(p):
    conds = []
    if _s(p, "company_domain"):
        conds.append(f"job_company_website='{_domain(p, 'company_domain')}'")
    titles = _list(p, "job_titles")
    if titles:
        conds.append("(" + " OR ".join(f"job_title='{t.lower()}'" for t in titles) + ")")
    locs = _list(p, "locations")
    if locs:
        conds.append("(" + " OR ".join(f"location_name LIKE '%{loc.lower()}%'" for loc in locs) + ")")
    if _s(p, "keywords"):
        raise InvalidInput("'keywords' is not supported with provider pdl; use apollo, or pass job_titles.")
    if not conds:
        raise InvalidInput("people_search with pdl needs job_titles, locations or company_domain.")
    return {"sql": "SELECT * FROM person WHERE " + " AND ".join(conds), "size": _int(p, "limit", 5, 1, 100)}


def _people_search_leadmagic(p):
    return _clean({
        "company_domain": _domain(p, "company_domain"),
        "titles": _list(p, "job_titles"),
        "limit": _int(p, "limit", 5, 1, 50),
    })


def _people_search_zoominfo(p):
    titles, domain = _list(p, "job_titles"), _s(p, "company_domain")
    if not (titles or domain):
        raise InvalidInput("people_search with zoominfo needs job_titles or company_domain.")
    return _clean({
        "jobTitle": " ".join(titles) or None,
        "companyWebsite": _domain(p, "company_domain") if domain else None,
        "pageSize": _int(p, "limit", 5, 1, 100),
    })


def _people_search_hunter(p):
    return _clean({"domain": _domain(p, "company_domain"), "limit": _int(p, "limit", 5, 1, 100)})


def _people_enrich_apollo(p):
    if _s(p, "linkedin_url"):
        return {"linkedin_url": _s(p, "linkedin_url")}
    if _s(p, "full_name") and _s(p, "company_domain"):
        return {"name": _s(p, "full_name"), "domain": _domain(p, "company_domain")}
    raise InvalidInput("enrich with apollo needs linkedin_url, or full_name plus company_domain.")


def _people_enrich_pdl(p):
    if _s(p, "email"):
        return {"email": _s(p, "email")}
    if _s(p, "linkedin_url"):
        return {"profile": _s(p, "linkedin_url")}
    if _s(p, "full_name") and (_s(p, "company_domain") or _s(p, "company_name")):
        return {"name": _s(p, "full_name"), "company": _s(p, "company_name") or _domain(p, "company_domain")}
    raise InvalidInput("enrich with pdl needs email, linkedin_url, or full_name plus company_domain.")


def _people_enrich_hunter(p):
    if _s(p, "email"):
        return {"email": _s(p, "email")}
    if _s(p, "linkedin_url"):
        return {"linkedin_handle": _linkedin_handle(_s(p, "linkedin_url"))}
    raise InvalidInput("enrich with hunter needs email or linkedin_url.")


def _people_enrich_prospeo(p):
    if _s(p, "linkedin_url"):
        return {"linkedin_url": _s(p, "linkedin_url")}
    if _s(p, "email"):
        return {"email": _s(p, "email")}
    if _s(p, "full_name") and _s(p, "company_domain"):
        return {"full_name": _s(p, "full_name"), "company_website": _domain(p, "company_domain")}
    raise InvalidInput("enrich with prospeo needs linkedin_url, email, or full_name plus company_domain.")


def _people_enrich_leadmagic(p):
    return {"profile_url": _need(p, "linkedin_url", "with provider leadmagic")}


def _find_email_hunter(p):
    return {"domain": _domain(p, "company_domain"), "full_name": _need(p, "full_name")}


def _find_email_leadmagic(p):
    first, last = _split_name(_need(p, "full_name"))
    return {"domain": _domain(p, "company_domain"), "first_name": first, "last_name": last}


def _find_email_prospeo(p):
    return {"full_name": _need(p, "full_name"), "company_website": _domain(p, "company_domain")}


# ------------------------------------------------------ company_intelligence


def _dfs_loc(p):
    return geo.dataforseo_location(_s(p, "country"))


def _company_traffic_dataforseo(p):
    loc, lang = _dfs_loc(p)
    return {"targets": [_domain(p)], "language_code": lang, "location_code": loc}


def _company_traffic_ahrefs(p):
    return _clean({"target": _domain(p), "date": _month_start(), "country": geo.ahrefs_country(_s(p, "country")) if _s(p, "country") else None})


def _company_competitors_dataforseo(p):
    loc, lang = _dfs_loc(p)
    return {"target": _domain(p), "language_code": lang, "location_code": loc, "limit": _int(p, "limit", 10, 1, 100)}


def _company_competitors_ahrefs(p):
    return {"target": _domain(p), "date": _month_start(), "country": geo.ahrefs_country(_s(p, "country")), "limit": _int(p, "limit", 10, 1, 25)}


def _company_competitors_serpstat(p):
    return {"se": geo.serpstat_database(_s(p, "country")), "domain": _domain(p), "size": _int(p, "limit", 10, 1, 100)}


# --------------------------------------------------------------- seo_research


def _keywords(p) -> list[str]:
    kws = _list(p, "keywords")
    if not kws:
        raise InvalidInput("'keywords' is required.")
    return kws


def _seo_kw_overview_semrush(p):
    kws = _keywords(p)
    return {"keyword": kws[0], "country": geo.semrush_country(_s(p, "country"))}


def _seo_kw_overview_dataforseo(p):
    loc, lang = _dfs_loc(p)
    return {"keywords": _keywords(p)[:100], "language_code": lang, "location_code": loc}


def _seo_kw_overview_ahrefs(p):
    return {"keywords": ",".join(_keywords(p)[:10]), "country": geo.ahrefs_country(_s(p, "country"))}


def _seo_kw_overview_serpstat(p):
    return {"se": geo.serpstat_database(_s(p, "country")), "keywords": _keywords(p)[:10]}


def _seo_kw_ideas_dataforseo(p):
    loc, lang = _dfs_loc(p)
    return {"keyword": _keywords(p)[0], "language_code": lang, "location_code": loc, "limit": _int(p, "limit", 20, 1, 1000)}


def _seo_kw_ideas_ahrefs(p):
    return {"keywords": _keywords(p)[0], "country": geo.ahrefs_country(_s(p, "country")), "limit": _int(p, "limit", 20, 1, 25)}


def _seo_kw_ideas_serpstat(p):
    return {"se": geo.serpstat_database(_s(p, "country")), "keyword": _keywords(p)[0], "size": _int(p, "limit", 20, 1, 1000)}


def _seo_domain_overview_dataforseo(p):
    loc, lang = _dfs_loc(p)
    return {"target": _domain(p), "language_code": lang, "location_code": loc}


def _seo_domain_overview_serpstat(p):
    return {"se": geo.serpstat_database(_s(p, "country")), "domains": [_domain(p)]}


def _seo_ranked_dataforseo(p):
    loc, lang = _dfs_loc(p)
    return {"target": _domain(p), "language_code": lang, "location_code": loc, "limit": _int(p, "limit", 20, 1, 1000)}


def _seo_ranked_ahrefs(p):
    return _clean({"target": _domain(p), "date": _month_start(), "country": geo.ahrefs_country(_s(p, "country")) if _s(p, "country") else None, "limit": _int(p, "limit", 20, 1, 25)})


def _seo_ranked_serpstat(p):
    return {"se": geo.serpstat_database(_s(p, "country")), "domain": _domain(p), "size": _int(p, "limit", 20, 1, 1000)}


def _semrush_scope(p, with_limit: bool):
    body = {"url": _domain(p), "scope": "ROOT_DOMAIN"}
    if with_limit:
        body["limit"] = _int(p, "limit", 20, 1, 100)
    return body


def _seo_serp_dataforseo(p):
    loc, lang = _dfs_loc(p)
    return {"keyword": _keywords(p)[0], "language_code": lang, "location_code": loc, "depth": _int(p, "limit", 10, 1, 100)}


def _seo_serp_serper(p):
    return _clean({"q": _keywords(p)[0], "gl": geo.iso2(_s(p, "country")) if _s(p, "country") else None, "num": _int(p, "limit", 10, 1, 100)})


# --------------------------------------------------------------- web_research


def _web_q(p):
    return _clean({"q": _need(p, "query"), "gl": geo.iso2(_s(p, "country")) if _s(p, "country") else None, "hl": _s(p, "language")})


def _web_q_num(p):
    return _clean({**_web_q(p), "num": _int(p, "limit", 10, 1, 100)})


def _web_search_exa(p):
    return {"query": _need(p, "query"), "numResults": _int(p, "limit", 10, 1, 100)}


def _web_scrape_serper(p):
    return {"url": _need(p, "url"), "includeMarkdown": True}


def _web_scrape_exa(p):
    return {"urls": [_need(p, "url")], "maxCharacters": 20000}


def _web_scrape_dataforseo(p):
    return {"url": _need(p, "url"), "markdown_view": True}


def _web_maps_serpapi(p):
    return _clean({"q": _need(p, "query"), "hl": _s(p, "language")})


def _web_scholar_serpapi(p):
    return _clean({"q": _need(p, "query"), "hl": _s(p, "language")})


def _web_answer_exa(p):
    return {"query": _need(p, "query")}


def _web_similar_exa(p):
    return {"url": _need(p, "url"), "numResults": _int(p, "limit", 10, 1, 100)}


# ------------------------------------------------------------ social_research


def _sc_query(p):
    return {"query": _need(p, "query")}


def _sc_handle(p):
    return {"handle": _need(p, "handle").lstrip("@")}


def _sc_url(p):
    return {"url": _need(p, "url")}


def _sc_subreddit(p):
    return {"subreddit": _need(p, "handle").lstrip("r/").lstrip("@")}


def _sc_find_profiles(p):
    platform = (_s(p, "platform") or "").lower()
    if platform not in {"instagram", "tiktok", "youtube", "x", "twitter", "facebook"}:
        raise InvalidInput("'platform' must be one of instagram, tiktok, youtube, x, twitter, facebook.")
    return {"handle": _need(p, "handle").lstrip("@"), "platform": platform}


def _apify_subreddit(p):
    sub = _need(p, "handle").lstrip("r/").lstrip("@")
    return {"startUrls": [{"url": f"https://www.reddit.com/r/{sub}/"}]}


def _apify_queries(p):
    return {"searchQueries": [_need(p, "query")]}


def _apify_usernames(p):
    return {"usernames": [_need(p, "handle").lstrip("@")]}


# --------------------------------------------------------------- the table

ROUTES: dict[str, dict[str, dict[str, Route]]] = {
    "people_search": {
        "search": {
            "apollo": Route("apollo", "/api/v1/mixed_people/api_search", 1, _people_search_apollo),
            "pdl": Route("pdl", "/v5/person/search", 1, _people_search_pdl),
            "leadmagic": Route("leadmagic", "/v3/people/search", 1, _people_search_leadmagic, "needs company_domain"),
            "zoominfo": Route("zoominfo", "/gtm/data/v1/contacts/search", 1, _people_search_zoominfo),
            "hunter": Route("hunter", "/v2/domain-search", 1, _people_search_hunter, "lists the addresses found at company_domain; job_titles are ignored"),
        },
        "enrich": {
            "apollo": Route("apollo", "/api/v1/people/match", 1, _people_enrich_apollo),
            "pdl": Route("pdl", "/v5/person/enrich", 6, _people_enrich_pdl),
            "hunter": Route("hunter", "/v2/people/find", 1, _people_enrich_hunter),
            "prospeo": Route("prospeo", "/enrich-person", 2, _people_enrich_prospeo),
            "leadmagic": Route("leadmagic", "/v1/people/profile-search", 1, _people_enrich_leadmagic),
        },
        "find_email": {
            "hunter": Route("hunter", "/v2/email-finder", 1, _find_email_hunter),
            "leadmagic": Route("leadmagic", "/v1/people/email-finder", 1, _find_email_leadmagic),
            "prospeo": Route("prospeo", "/enrich-person", 2, _find_email_prospeo),
            "apollo": Route("apollo", "/api/v1/people/match", 1, _people_enrich_apollo),
        },
    },
    "company_intelligence": {
        "enrich": {
            "apollo": Route("apollo", "/api/v1/organizations/enrich", 1, lambda p: {"domain": _domain(p)}),
            "pdl": Route("pdl", "/v5/company/enrich", 3, lambda p: {"website": _domain(p)}),
            "hunter": Route("hunter", "/v2/companies/find", 1, lambda p: {"domain": _domain(p)}),
            "prospeo": Route("prospeo", "/enrich-company", 2, lambda p: {"company_website": _domain(p)}),
            "predictleads": Route("predictleads", "/companies/{id_or_domain}", 2, lambda p: {"domain": _domain(p)}),
            "leadmagic": Route("leadmagic", "/v1/companies/company-search", 1, lambda p: {"company_domain": _domain(p)}),
        },
        "tech_stack": {
            "builtwith": Route("builtwith", "/v23/api.json", 1, lambda p: {"LOOKUP": _domain(p), "NOPII": "yes", "NOATTR": "yes", "NOMETA": "yes"}),
            "predictleads": Route("predictleads", "/companies/{company_id_or_domain}/technology_detections", 3, lambda p: {"domain": _domain(p), "limit": _int(p, "limit", 20, 1, 100)}),
            "dataforseo": Route("dataforseo", "/v3/domain_analytics/technologies/domain_technologies/live", 2, lambda p: {"target": _domain(p)}),
        },
        "traffic": {
            "dataforseo": Route("dataforseo", "/v3/dataforseo_labs/google/bulk_traffic_estimation/live", 2, _company_traffic_dataforseo),
            "ahrefs": Route("ahrefs", "/v3/site-explorer/metrics", 2, _company_traffic_ahrefs),
            "apify": Route("apify", "/tri_angle/fast-similarweb-scraper", 1, lambda p: {"website": _domain(p)}, "Similarweb figures; async"),
        },
        "competitors": {
            "dataforseo": Route("dataforseo", "/v3/dataforseo_labs/google/competitors_domain/live", 2, _company_competitors_dataforseo),
            "ahrefs": Route("ahrefs", "/v3/site-explorer/organic-competitors", 2, _company_competitors_ahrefs),
            "serpstat": Route("serpstat", "/v4/SerpstatDomainProcedure.getOrganicCompetitorsPage", 1, _company_competitors_serpstat),
            "predictleads": Route("predictleads", "/companies/{company_id_or_domain}/similar_companies", 1, lambda p: {"domain": _domain(p), "limit": _int(p, "limit", 10, 1, 100)}),
        },
        "funding": {
            "predictleads": Route("predictleads", "/companies/{company_id_or_domain}/financing_events", 2, lambda p: {"domain": _domain(p), "limit": _int(p, "limit", 10, 1, 100)}),
            "leadmagic": Route("leadmagic", "/v1/companies/company-funding", 1, lambda p: {"company_domain": _domain(p)}),
        },
        "news": {
            "predictleads": Route("predictleads", "/companies/{company_id_or_domain}/news_events", 2, lambda p: {"domain": _domain(p), "limit": _int(p, "limit", 10, 1, 100)}),
            "serper": Route("serper", "/news", 2, lambda p: {"q": _s(p, "query") or _domain(p)}),
        },
    },
    "seo_research": {
        "keyword_overview": {
            "semrush": Route("semrush", "/apis/v4/keywords/v1/metrics", 2, _seo_kw_overview_semrush, "one keyword per call"),
            "serpstat": Route("serpstat", "/v4/SerpstatKeywordProcedure.getKeywordsInfo", 2, _seo_kw_overview_serpstat, "up to 10 keywords"),
            "dataforseo": Route("dataforseo", "/v3/keywords_data/google_ads/search_volume/live", 2, _seo_kw_overview_dataforseo),
            "ahrefs": Route("ahrefs", "/v3/keywords-explorer/overview", 2, _seo_kw_overview_ahrefs, "up to 10 keywords"),
        },
        "keyword_ideas": {
            "dataforseo": Route("dataforseo", "/v3/dataforseo_labs/google/keyword_suggestions/live", 2, _seo_kw_ideas_dataforseo),
            "serpstat": Route("serpstat", "/v4/SerpstatKeywordProcedure.getRelatedKeywords", 2, _seo_kw_ideas_serpstat),
            "ahrefs": Route("ahrefs", "/v3/keywords-explorer/matching-terms", 2, _seo_kw_ideas_ahrefs),
        },
        "domain_overview": {
            "dataforseo": Route("dataforseo", "/v3/dataforseo_labs/google/domain_rank_overview/live", 2, _seo_domain_overview_dataforseo),
            "serpstat": Route("serpstat", "/v4/SerpstatDomainProcedure.getDomainsInfo", 3, _seo_domain_overview_serpstat),
            "ahrefs": Route("ahrefs", "/v3/site-explorer/metrics", 2, _company_traffic_ahrefs),
        },
        "ranked_keywords": {
            "dataforseo": Route("dataforseo", "/v3/dataforseo_labs/google/ranked_keywords/live", 2, _seo_ranked_dataforseo),
            "serpstat": Route("serpstat", "/v4/SerpstatDomainProcedure.getDomainKeywords", 2, _seo_ranked_serpstat),
            "ahrefs": Route("ahrefs", "/v3/site-explorer/organic-keywords", 2, _seo_ranked_ahrefs),
        },
        "backlinks_overview": {
            "semrush": Route("semrush", "/apis/v4/backlinks/v1/overview", 2, lambda p: _semrush_scope(p, False)),
            "dataforseo": Route("dataforseo", "/v3/backlinks/summary/live", 2, lambda p: {"target": _domain(p)}),
            "ahrefs": Route("ahrefs", "/v3/site-explorer/backlinks-stats", 2, lambda p: {"target": _domain(p), "date": _month_start()}),
            "serpstat": Route("serpstat", "/v4/SerpstatBacklinksProcedure.getSummaryV2", 3, lambda p: {"query": _domain(p), "searchType": "domain_with_subdomains"}),
        },
        "backlinks": {
            "semrush": Route("semrush", "/apis/v4/backlinks/v1/links", 1, lambda p: _semrush_scope(p, True)),
            "dataforseo": Route("dataforseo", "/v3/backlinks/backlinks/live", 3, lambda p: {"target": _domain(p), "limit": _int(p, "limit", 20, 1, 1000), "mode": "one_per_domain"}),
            "ahrefs": Route("ahrefs", "/v3/site-explorer/all-backlinks", 2, lambda p: {"target": _domain(p), "limit": _int(p, "limit", 20, 1, 50)}),
        },
        "referring_domains": {
            "semrush": Route("semrush", "/apis/v4/backlinks/v1/ref-domains", 1, lambda p: _semrush_scope(p, True)),
            "dataforseo": Route("dataforseo", "/v3/backlinks/referring_domains/live", 2, lambda p: {"target": _domain(p), "limit": _int(p, "limit", 20, 1, 1000)}),
            "ahrefs": Route("ahrefs", "/v3/site-explorer/refdomains", 2, lambda p: {"target": _domain(p), "limit": _int(p, "limit", 20, 1, 50)}),
        },
        "domain_rating": {
            "ahrefs": Route("ahrefs", "/v3/public/domain-rating-free", 1, lambda p: {"target": _domain(p)}),
        },
        "serp": {
            "dataforseo": Route("dataforseo", "/v3/serp/google/organic/live/advanced", 2, _seo_serp_dataforseo),
            "serper": Route("serper", "/search", 2, _seo_serp_serper),
        },
    },
    "web_research": {
        "search": {
            "serper": Route("serper", "/search", 2, _web_q_num),
            "serpapi": Route("serpapi", "/search?engine=google", 2, _web_q),
            "exa": Route("exa", "/search", 1, _web_search_exa, "neural search by meaning"),
        },
        "news": {
            "serper": Route("serper", "/news", 2, _web_q),
            "serpapi": Route("serpapi", "/search?engine=google_news", 1, _web_q),
        },
        "scrape": {
            "serper": Route("serper", "/scrape", 3, _web_scrape_serper),
            "exa": Route("exa", "/contents", 1, _web_scrape_exa),
            "dataforseo": Route("dataforseo", "/v3/on_page/content_parsing/live", 1, _web_scrape_dataforseo),
        },
        "places": {
            "serper": Route("serper", "/places", 2, _web_q),
            "serpapi": Route("serpapi", "/search?engine=google_maps", 2, _web_maps_serpapi),
        },
        "scholar": {
            "serper": Route("serper", "/scholar", 2, _web_q),
            "serpapi": Route("serpapi", "/search?engine=google_scholar", 2, _web_scholar_serpapi),
        },
        "shopping": {
            "serper": Route("serper", "/shopping", 2, _web_q),
            "serpapi": Route("serpapi", "/search?engine=google_shopping", 2, _web_q),
        },
        "images": {
            "serper": Route("serper", "/images", 2, _web_q_num),
        },
        "videos": {
            "serper": Route("serper", "/videos", 2, _web_q),
        },
        "answer": {
            "exa": Route("exa", "/answer", 1, _web_answer_exa),
        },
        "similar": {
            "exa": Route("exa", "/findSimilar", 1, _web_similar_exa),
        },
    },
    "social_research": {
        "reddit_search": {
            "scrapecreators": Route("scrapecreators", "/v1/reddit/search", 2, _sc_query),
        },
        "reddit_subreddit": {
            "scrapecreators": Route("scrapecreators", "/v1/reddit/subreddit", 2, _sc_subreddit),
            "apify": Route("apify", "/practicaltools/apify-reddit-api", 1, _apify_subreddit, "async"),
        },
        "x_user_tweets": {
            "scrapecreators": Route("scrapecreators", "/v1/twitter/user-tweets", 2, _sc_handle),
        },
        "x_tweet": {
            "scrapecreators": Route("scrapecreators", "/v1/twitter/tweet", 2, _sc_url),
        },
        "youtube_search": {
            "scrapecreators": Route("scrapecreators", "/v1/youtube/search", 2, _sc_query),
            "apify": Route("apify", "/streamers/youtube-scraper", 1, _apify_queries, "async"),
        },
        "youtube_channel": {
            "scrapecreators": Route("scrapecreators", "/v1/youtube/channel-videos", 2, _sc_handle),
        },
        "tiktok_search": {
            "scrapecreators": Route("scrapecreators", "/v1/tiktok/search/keyword", 2, _sc_query),
        },
        "instagram_profile": {
            "scrapecreators": Route("scrapecreators", "/v1/instagram/profile", 2, _sc_handle),
            "apify": Route("apify", "/apify/instagram-profile-scraper", 1, _apify_usernames, "async"),
        },
        "linkedin_posts": {
            "scrapecreators": Route("scrapecreators", "/v1/linkedin/search/posts", 2, _sc_query),
            "apify": Route("apify", "/harvestapi/linkedin-post-search", 1, _apify_queries, "async"),
        },
        "linkedin_profile": {
            "scrapecreators": Route("scrapecreators", "/v1/linkedin/profile", 2, _sc_url),
            "tikhub": Route("tikhub", "/api/v1/linkedin/web_v2/get_user_profile", 2, _sc_url),
        },
        "linkedin_company": {
            "scrapecreators": Route("scrapecreators", "/v1/linkedin/company", 2, _sc_url),
        },
        "find_profiles": {
            "scrapecreators": Route("scrapecreators", "/v1/find-social-profiles", 2, _sc_find_profiles),
        },
    },
}

# provider = auto resolves here. Chosen for price and coverage on 2026-09-17.
AUTO: dict[str, dict[str, Any]] = {
    "people_search": {"search": "apollo", "enrich": "apollo", "find_email": "hunter"},
    "company_intelligence": {
        "enrich": "apollo", "tech_stack": "builtwith", "traffic": "dataforseo",
        "competitors": "dataforseo", "funding": "predictleads", "news": "predictleads",
    },
    "seo_research": {
        # semrush takes one keyword per call; several keywords go to serpstat.
        "keyword_overview": lambda p: "semrush" if len(_list(p, "keywords")) <= 1 else "serpstat",
        "keyword_ideas": "dataforseo", "domain_overview": "dataforseo",
        "ranked_keywords": "dataforseo", "backlinks_overview": "semrush", "backlinks": "semrush",
        "referring_domains": "semrush", "domain_rating": "ahrefs", "serp": "dataforseo",
    },
    "web_research": {
        "search": "serper", "news": "serper", "scrape": "serper", "places": "serper",
        "scholar": "serper", "shopping": "serper", "images": "serper", "videos": "serper",
        "answer": "exa", "similar": "exa",
    },
    "social_research": {action: "scrapecreators" for action in ROUTES["social_research"]},
}


def providers_for(tool: str) -> list[str]:
    """Every provider the tool's select lists, auto first."""
    seen: list[str] = []
    for routes in ROUTES[tool].values():
        for provider in routes:
            if provider not in seen:
                seen.append(provider)
    return ["auto", *seen]


def resolve(tool: str, action: Optional[str], provider: Optional[str], params: dict[str, Any]) -> tuple[Route, str]:
    """The route for (tool, action, provider). Returns (route, provider used)."""
    actions = ROUTES[tool]
    action = (action or "").strip()
    if action not in actions:
        raise InvalidInput(f"'action' must be one of: {', '.join(actions)}.")
    chosen = (provider or "auto").strip().lower() or "auto"
    if chosen == "auto":
        pick = AUTO[tool][action]
        chosen = pick(params) if callable(pick) else pick
    routes = actions[action]
    if chosen not in routes:
        raise InvalidInput(
            f"action '{action}' is not served by provider '{chosen}'. "
            f"Providers for it: {', '.join(routes)} (or auto)."
        )
    return routes[chosen], chosen
