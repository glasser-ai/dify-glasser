"""Routing table tests: every (action, provider) builds a provider-native
input from the flat parameters, or refuses before any API call."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import routes  # noqa: E402
from utils.routes import InvalidInput, resolve  # noqa: E402


def build(tool, action, provider="auto", **params):
    params = {"action": action, "provider": provider, **params}
    route, used = resolve(tool, action, provider, params)
    return used, route, route.build(params)


def test_every_tool_has_an_auto_for_every_action():
    for tool, actions in routes.ROUTES.items():
        for action, providers in actions.items():
            pick = routes.AUTO[tool][action]
            if callable(pick):
                pick = pick({})
            assert pick in providers, (tool, action, pick)


def test_unknown_action_and_unsupported_provider_are_refused():
    with pytest.raises(InvalidInput):
        resolve("people_search", "nope", "auto", {})
    with pytest.raises(InvalidInput):
        resolve("people_search", "find_email", "zoominfo", {})


def test_people_search_apollo_auto():
    used, route, body = build("people_search", "search", job_titles="CTO, VP Engineering", company_domain="https://www.stripe.com/", limit=3)
    assert used == "apollo" and route.endpoint == "/api/v1/mixed_people/api_search"
    assert body == {"per_page": 3, "person_titles[]": ["CTO", "VP Engineering"], "q_organization_domains_list[]": ["stripe.com"]}


def test_people_search_pdl_builds_sql():
    _, _, body = build("people_search", "search", "pdl", job_titles="cto", company_domain="stripe.com", locations="london")
    assert body["sql"] == "SELECT * FROM person WHERE job_company_website='stripe.com' AND (job_title='cto') AND (location_name LIKE '%london%')"
    assert body["size"] == 5
    with pytest.raises(InvalidInput):
        build("people_search", "search", "pdl", keywords="x", company_domain="stripe.com")


def test_people_search_needs_a_filter():
    with pytest.raises(InvalidInput):
        build("people_search", "search")


def test_people_enrich_routes():
    assert build("people_search", "enrich", linkedin_url="https://linkedin.com/in/patrickcollison")[2] == {"linkedin_url": "https://linkedin.com/in/patrickcollison"}
    assert build("people_search", "enrich", "pdl", email="a@b.com")[2] == {"email": "a@b.com"}
    assert build("people_search", "enrich", "hunter", linkedin_url="https://www.linkedin.com/in/williamhgates/")[2] == {"linkedin_handle": "williamhgates"}
    with pytest.raises(InvalidInput):
        build("people_search", "enrich", "hunter", full_name="x y", company_domain="z.com")


def test_find_email_routes():
    assert build("people_search", "find_email", full_name="Patrick Collison", company_domain="stripe.com") == (
        "hunter", routes.ROUTES["people_search"]["find_email"]["hunter"], {"domain": "stripe.com", "full_name": "Patrick Collison"})
    assert build("people_search", "find_email", "leadmagic", full_name="Patrick Collison", company_domain="stripe.com")[2] == {"domain": "stripe.com", "first_name": "Patrick", "last_name": "Collison"}
    with pytest.raises(InvalidInput):
        build("people_search", "find_email", "leadmagic", full_name="Cher", company_domain="stripe.com")


def test_company_routes():
    assert build("company_intelligence", "enrich", domain="stripe.com")[2] == {"domain": "stripe.com"}
    assert build("company_intelligence", "enrich", "pdl", domain="stripe.com")[2] == {"website": "stripe.com"}
    assert build("company_intelligence", "tech_stack", domain="shopify.com")[2] == {"LOOKUP": "shopify.com", "NOPII": "yes", "NOATTR": "yes", "NOMETA": "yes"}
    used, _, body = build("company_intelligence", "traffic", domain="stripe.com", country="de")
    assert used == "dataforseo" and body == {"targets": ["stripe.com"], "language_code": "de", "location_code": 2276}
    _, _, body = build("company_intelligence", "competitors", "ahrefs", domain="stripe.com", country="gb", limit=5)
    assert body["country"] == "gb" and body["limit"] == 5 and body["date"].endswith("-01")
    with pytest.raises(InvalidInput):
        build("company_intelligence", "enrich", domain="not a domain")


def test_seo_routes():
    used, _, body = build("seo_research", "keyword_overview", keywords="espresso machine", country="gb")
    assert used == "semrush" and body == {"keyword": "espresso machine", "country": "UK"}
    assert build("seo_research", "keyword_overview", keywords="x", country="UK")[2]["country"] == "UK"
    assert build("seo_research", "keyword_overview", keywords="x", country="de")[2]["country"] == "DE"
    used, _, body = build("seo_research", "keyword_overview", keywords="a, b, c")
    assert used == "serpstat" and body == {"se": "g_us", "keywords": ["a", "b", "c"]}
    _, _, body = build("seo_research", "keyword_ideas", keywords="phone", limit=7)
    assert body == {"keyword": "phone", "language_code": "en", "location_code": 2840, "limit": 7}
    _, _, body = build("seo_research", "backlinks", domain="stripe.com", limit=5)
    assert body == {"url": "stripe.com", "scope": "ROOT_DOMAIN", "limit": 5}
    _, _, body = build("seo_research", "domain_rating", domain="https://glasser.ai/docs")
    assert body == {"target": "glasser.ai"}
    with pytest.raises(InvalidInput):
        build("seo_research", "keyword_overview")


def test_web_routes():
    used, _, body = build("web_research", "search", query="vector db", country="de", limit=5)
    assert used == "serper" and body == {"q": "vector db", "gl": "de", "num": 5}
    assert build("web_research", "scrape", url="https://example.com")[2] == {"url": "https://example.com", "includeMarkdown": True}
    assert build("web_research", "answer", query="q")[1].provider == "exa"
    assert build("web_research", "search", "exa", query="q", limit=3)[2] == {"query": "q", "numResults": 3}
    with pytest.raises(InvalidInput):
        build("web_research", "scrape", query="no url")


def test_social_routes():
    assert build("social_research", "reddit_subreddit", handle="r/javascript")[2] == {"subreddit": "javascript"}
    assert build("social_research", "reddit_subreddit", "apify", handle="javascript")[2] == {"startUrls": [{"url": "https://www.reddit.com/r/javascript/"}]}
    assert build("social_research", "x_user_tweets", handle="@levelsio")[2] == {"handle": "levelsio"}
    assert build("social_research", "find_profiles", handle="natgeo", platform="Instagram")[2] == {"handle": "natgeo", "platform": "instagram"}
    with pytest.raises(InvalidInput):
        build("social_research", "find_profiles", handle="natgeo", platform="myspace")


def test_providers_for_lists_auto_first():
    assert routes.providers_for("web_research")[0] == "auto"
    assert set(routes.providers_for("seo_research")) == {"auto", "semrush", "serpstat", "dataforseo", "ahrefs", "serper"}
