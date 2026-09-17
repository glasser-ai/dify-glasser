"""Country and language codes in the forms each provider wants.

The capability tools take one `country` parameter as a two-letter ISO code
(e.g. "us", "de"). Providers spell it differently: DataForSEO wants a
numeric location_code plus a language_code, Serpstat a database name
such as g_us, Ahrefs a lowercase ISO code, Semrush an uppercase one.
"""

from typing import Optional

# ISO alpha-2 -> (DataForSEO location_code, default language_code)
_DATAFORSEO = {
    "us": (2840, "en"), "gb": (2826, "en"), "uk": (2826, "en"), "ca": (2124, "en"),
    "au": (2036, "en"), "nz": (2554, "en"), "ie": (2372, "en"), "in": (2356, "en"),
    "sg": (2702, "en"), "de": (2276, "de"), "at": (2040, "de"), "ch": (2756, "de"),
    "fr": (2250, "fr"), "be": (2056, "fr"), "es": (2724, "es"), "mx": (2484, "es"),
    "ar": (2032, "es"), "it": (2380, "it"), "nl": (2528, "nl"), "pt": (2620, "pt"),
    "br": (2076, "pt"), "jp": (2392, "ja"), "kr": (2410, "ko"), "cn": (2156, "zh-CN"),
    "hk": (2344, "zh-TW"), "tw": (2158, "zh-TW"), "ru": (2643, "ru"), "pl": (2616, "pl"),
    "se": (2752, "sv"), "no": (2578, "no"), "dk": (2208, "da"), "fi": (2246, "fi"),
    "tr": (2792, "tr"), "id": (2360, "id"), "th": (2764, "th"), "vn": (2704, "vi"),
    "ph": (2608, "en"), "my": (2458, "en"), "za": (2710, "en"), "ae": (2784, "en"),
    "il": (2376, "he"), "sa": (2682, "ar"), "eg": (2818, "ar"), "ng": (2566, "en"),
    "ua": (2804, "uk"), "cz": (2203, "cs"), "gr": (2300, "el"), "hu": (2348, "hu"),
    "ro": (2642, "ro"), "co": (2170, "es"), "cl": (2152, "es"), "pe": (2604, "es"),
}

_SERPSTAT = {
    "us": "g_us", "gb": "g_uk", "uk": "g_uk", "ca": "g_ca", "au": "g_au", "de": "g_de",
    "fr": "g_fr", "es": "g_es", "it": "g_it", "nl": "g_nl", "br": "g_br", "mx": "g_mx",
    "pl": "g_pl", "ua": "g_ua", "ru": "g_ru", "in": "g_in", "jp": "g_jp", "tr": "g_tr",
    "se": "g_se", "dk": "g_dk", "no": "g_no", "fi": "g_fi", "pt": "g_pt", "ie": "g_ie",
    "ch": "g_ch", "at": "g_at", "be": "g_be", "cz": "g_cz", "za": "g_za", "sg": "g_sg",
    "nz": "g_nz", "ar": "g_ar", "cl": "g_cl", "co": "g_co", "pe": "g_pe", "id": "g_id",
    "th": "g_th", "vn": "g_vn", "ph": "g_ph", "my": "g_my", "kr": "g_kr", "hk": "g_hk",
    "tw": "g_tw", "il": "g_il", "ae": "g_ae", "sa": "g_sa", "eg": "g_eg", "ng": "g_ng",
}


def iso2(country: Optional[str]) -> str:
    """Normalise a user-supplied country to lowercase alpha-2, default us."""
    code = (country or "").strip().lower()
    if code == "uk":
        return "gb"
    return code[:2] if len(code) >= 2 else "us"


def dataforseo_location(country: Optional[str]) -> tuple[int, str]:
    return _DATAFORSEO.get(iso2(country), _DATAFORSEO["us"])


def serpstat_database(country: Optional[str]) -> str:
    return _SERPSTAT.get(iso2(country), "g_us")


def ahrefs_country(country: Optional[str]) -> str:
    return iso2(country)


def semrush_country(country: Optional[str]) -> str:
    """Semrush spells the United Kingdom UK, not GB (verified against its docs)."""
    code = iso2(country)
    return "UK" if code == "gb" else code.upper()
