"""Generate tools/<capability>.yaml and utils/gtm_schema.py from the Glasser OpenAPI document.

The contract is the single truth for parameters: names, types, enums, which
are required, the default action, and the English description the model
reads all come from the request schema of POST /v1/solutions/gtm/<capability>.
This script only adds what Dify needs on top: labels and human descriptions
in four languages, which live in the tables below.

Run at development time, commit the output:

    uv run python scripts/gen_tools.py                       # reads the public document
    uv run python scripts/gen_tools.py ../glasser/packages/contract/openapi.json

Dify only ever sees the committed yaml; nothing is fetched at runtime.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_URL = "https://glasser.ai/docs/openapi.json"
SOLUTION = "gtm"
PATH_PREFIX = f"/v1/solutions/{SOLUTION}/"

L = lambda en, zh, ja, pt: {"en_US": en, "zh_Hans": zh, "ja_JP": ja, "pt_BR": pt}  # noqa: E731

# ---------------------------------------------------------------- tool copy
# Label, human description and the llm description of each tool. The llm
# text is what the agent reads to choose a tool; the human text is shown in
# the Dify UI.

TOOLS = {
    "web_research": dict(
        label=L("Web Research", "网络研究", "ウェブリサーチ", "Pesquisa na web"),
        human=L("Search the web, news and places, read page content, get answers with sources. Data from Serper and Exa.",
                "搜网页、新闻和地点，读取页面内容，得到带来源的答案。数据来自 Serper 与 Exa。",
                "ウェブ、ニュース、場所を検索し、ページ本文を読み取り、出典付きの回答を得る。データはSerperとExaから。",
                "Pesquise a web, notícias e lugares, leia o conteúdo de páginas, obtenha respostas com fontes. Dados da Serper e Exa."),
        llm="Search the web, news, places, scholar, shopping, images or videos; read a web page; get an answer with sources. Use this when the user needs live information from the internet.",
    ),
    "company_intelligence": dict(
        label=L("Company Intelligence", "公司情报", "企業インテリジェンス", "Inteligência de empresas"),
        human=L("From a domain, get the company profile, tech stack, website traffic, competitors, funding and news. Data from Apollo, BuiltWith and PredictLeads.",
                "输入域名，得到公司档案、技术栈、网站流量、竞争对手、融资与新闻。数据来自 Apollo、BuiltWith 与 PredictLeads。",
                "ドメインから企業プロフィール、技術スタック、サイトトラフィック、競合、資金調達、ニュースを取得。データはApollo、BuiltWith、PredictLeadsから。",
                "A partir de um domínio, obtenha perfil da empresa, stack de tecnologia, tráfego do site, concorrentes, investimentos e notícias. Dados da Apollo, BuiltWith e PredictLeads."),
        llm="Company profile, technology stack, website traffic, competitors, funding and news for one domain. Use this when the user asks about a company by its website.",
    ),
    "people_search": dict(
        label=L("Find Prospects", "客户开发", "プロスペクト検索", "Prospecção"),
        human=L("Find contacts by title, location or company, enrich a profile, get a work email. Data from Apollo and People Data Labs.",
                "按职位、地区或公司找到联系人，补全资料，拿到工作邮箱。数据来自 Apollo 与 People Data Labs。",
                "役職・所在地・企業で連絡先を探し、プロフィールを補完し、仕事用メールを取得。データはApolloとPeople Data Labsから。",
                "Encontre contatos por cargo, localização ou empresa, enriqueça um perfil, obtenha um e-mail de trabalho. Dados da Apollo e People Data Labs."),
        llm="Find B2B professionals and decision makers, enrich one person, or find a work email. Use this when the user needs people matching a title, seniority, location or company, or details about one known person.",
    ),
    "seo_research": dict(
        label=L("Keywords & SEO", "关键词与 SEO", "キーワードとSEO", "Palavras-chave e SEO"),
        human=L("Keyword volume and difficulty, keyword ideas, domain traffic and ranking keywords, backlinks, domain rating. Data from Semrush and Ahrefs.",
                "查关键词搜索量与难度、拓展词、域名流量与排名词、外链、域名评分。数据来自 Semrush 与 Ahrefs。",
                "キーワードのボリュームと難易度、キーワード候補、ドメインのトラフィックとランキングキーワード、被リンク、ドメインレーティング。データはSemrushとAhrefsから。",
                "Volume e dificuldade de palavras-chave, ideias de palavras-chave, tráfego e palavras-chave de um domínio, backlinks, domain rating. Dados da Semrush e Ahrefs."),
        llm="Keyword volume and difficulty, keyword ideas, a domain's organic traffic, ranking keywords, backlinks and domain rating. Use this when the user asks for SEO metrics of a keyword or a domain.",
    ),
    "social_research": dict(
        label=L("Social Media Search", "社交媒体搜索", "SNS検索", "Busca em redes sociais"),
        human=L("Search posts, profiles and channels on Reddit, X, YouTube, TikTok, Instagram and LinkedIn, read-only. Data from ScrapeCreators.",
                "搜 Reddit、X、YouTube、TikTok、Instagram、LinkedIn 上的帖子、主页与频道，只读。数据来自 ScrapeCreators。",
                "Reddit、X、YouTube、TikTok、Instagram、LinkedInの投稿、プロフィール、チャンネルを検索。読み取り専用。データはScrapeCreatorsから。",
                "Pesquise posts, perfis e canais no Reddit, X, YouTube, TikTok, Instagram e LinkedIn, somente leitura. Dados da ScrapeCreators."),
        llm="Search posts, profiles and channels on Reddit, X, YouTube, TikTok, Instagram and LinkedIn. Use this when the user asks what people say on social media or about a social account.",
    ),
    "market_data": dict(
        label=L("Market Data", "市场数据", "マーケットデータ", "Dados de mercado"),
        human=L("US property values, rent estimates, listings and ZIP-code market statistics, plus stock quotes. Data from RentCast and SerpApi.",
                "美国房产估值、租金估算、房源与邮编市场统计，以及股票行情。数据来自 RentCast 与 SerpApi。",
                "米国の不動産価値、家賃の推定、物件情報、ZIPコード別の市場統計、および株価。データはRentCastとSerpApiから。",
                "Valores de imóveis nos EUA, estimativas de aluguel, anúncios e estatísticas de mercado por CEP, além de cotações de ações. Dados da RentCast e SerpApi."),
        llm="US property value and rent estimates, property records, for-sale and rental listings, ZIP-code market statistics, and a stock quote by symbol. Use this when the user asks about a US address, a local housing market, or a stock price.",
    ),
}

# ----------------------------------------------------------- parameter copy
# Label and human description per parameter name. The llm description comes
# from the OpenAPI schema when the contract gives one, else from the English
# text here.

PARAMS = {
    "action": (L("Action", "操作", "アクション", "Ação"),
               L("What to do; see the tool description.", "要做的事；见工具说明。", "実行内容。ツールの説明を参照。", "O que fazer; veja a descrição da ferramenta.")),
    "provider": (L("Provider", "数据来源", "プロバイダー", "Provider"),
                 L("Which data provider to use. Auto lets Glasser pick a good default for the action.", "使用哪家数据提供方。auto 由 Glasser 为该操作选择默认来源。", "使用するデータプロバイダー。autoならGlasserがアクションに応じて選択。", "Qual provedor de dados usar. Auto deixa o Glasser escolher um bom padrão para a ação.")),
    "platform": (L("Platform", "平台", "プラットフォーム", "Plataforma"),
                 L("The social network to search.", "要搜索的社交平台。", "検索するSNS。", "A rede social a pesquisar.")),
    "mode": (L("Mode", "模式", "モード", "Modo"),
             L("What to fetch; see the tool description.", "要获取的内容；见工具说明。", "取得する内容。ツールの説明を参照。", "O que buscar; veja a descrição da ferramenta.")),
    "query": (L("Query", "查询", "クエリ", "Consulta"),
              L("Search phrase or question.", "搜索词或问题。", "検索語または質問。", "Termo de busca ou pergunta.")),
    "url": (L("URL", "URL", "URL", "URL"),
            L("A full http(s) URL.", "完整的 http(s) URL。", "完全なhttp(s) URL。", "Uma URL http(s) completa.")),
    "domain": (L("Domain", "域名", "ドメイン", "Domínio"),
               L("A company website domain, e.g. stripe.com.", "公司网站域名，如 stripe.com。", "企業サイトのドメイン（例: stripe.com）。", "O domínio do site da empresa, por exemplo stripe.com.")),
    "keywords": (L("Keywords", "关键词", "キーワード", "Palavras-chave"),
                 L("Keywords to look up, e.g. 'espresso machine'.", "要查的关键词，如 'espresso machine'。", "調べるキーワード（例: 'espresso machine'）。", "Palavras-chave a consultar, por exemplo 'espresso machine'.")),
    "people_search.keywords": (L("Keywords", "关键词", "キーワード", "Palavras-chave"),
                               L("Free-text keywords for people search.", "人物搜索的自由关键词。", "人物検索の自由キーワード。", "Palavras-chave livres para busca de pessoas.")),
    "country": (L("Country", "国家", "国", "País"),
                L("Two-letter country code or country name, e.g. us, gb, Germany (default us).", "两位国家代码或国家名，如 us、gb、Germany（默认 us）。", "2文字の国コードまたは国名（例: us, gb, Germany、デフォルトus）。", "Código de país de duas letras ou nome do país, por exemplo us, gb, Germany (padrão us).")),
    "language": (L("Language", "语言", "言語", "Idioma"),
                 L("Two-letter language code for the results, e.g. en, de.", "结果语言的两位代码，如 en、de。", "結果の言語コード（例: en, de）。", "Código de idioma de duas letras para os resultados, por exemplo en, de.")),
    "limit": (L("Limit", "数量", "件数", "Limite"),
              L("How many rows to return. Keep it small: the charge may depend on it.", "返回行数。保持小量：扣费可能与它相关。", "返す行数。少なめに：課金額が依存する場合があります。", "Quantas linhas retornar. Mantenha baixo: a cobrança pode depender disso.")),
    "job_titles": (L("Job titles", "职位", "役職", "Cargos"),
                   L("Job titles, e.g. 'CTO, VP Engineering'.", "职位，如 'CTO, VP Engineering'。", "役職（例: 'CTO, VP Engineering'）。", "Cargos, por exemplo 'CTO, VP Engineering'.")),
    "seniorities": (L("Seniorities", "级别", "役職レベル", "Senioridades"),
                    L("Seniority levels, e.g. 'c_suite, vp, director'.", "级别，如 'c_suite, vp, director'。", "役職レベル（例: 'c_suite, vp, director'）。", "Níveis de senioridade, por exemplo 'c_suite, vp, director'.")),
    "locations": (L("Locations", "地区", "所在地", "Localizações"),
                  L("Cities, states or countries.", "城市、州或国家。", "都市、州、国。", "Cidades, estados ou países.")),
    "company_domain": (L("Company domain", "公司域名", "企業ドメイン", "Domínio da empresa"),
                       L("The employer's website domain, e.g. stripe.com.", "雇主的网站域名，如 stripe.com。", "雇用主のサイトのドメイン（例: stripe.com）。", "O domínio do site do empregador, por exemplo stripe.com.")),
    "full_name": (L("Full name", "全名", "氏名", "Nome completo"),
                  L("The person's full name, e.g. 'Patrick Collison'.", "人物全名，如 'Patrick Collison'。", "人物の氏名（例: 'Patrick Collison'）。", "O nome completo da pessoa, por exemplo 'Patrick Collison'.")),
    "email": (L("Email", "邮箱", "メール", "E-mail"),
              L("The person's email address.", "人物的邮箱地址。", "人物のメールアドレス。", "O endereço de e-mail da pessoa.")),
    "linkedin_url": (L("LinkedIn URL", "LinkedIn 链接", "LinkedIn URL", "URL do LinkedIn"),
                     L("The person's LinkedIn profile URL.", "人物的 LinkedIn 个人主页链接。", "人物のLinkedInプロフィールURL。", "A URL do perfil do LinkedIn da pessoa.")),
    "handle": (L("Handle", "账号", "ハンドル", "Handle"),
               L("A username or handle without @, or a subreddit name.", "用户名或账号（不带 @），或 subreddit 名称。", "@なしのユーザー名またはハンドル、あるいはsubreddit名。", "Um nome de usuário ou handle sem @, ou o nome de um subreddit.")),
    "address": (L("Address", "地址", "住所", "Endereço"),
                L("US street address, e.g. '5500 Grand Lake Dr, San Antonio, TX 78244'.", "美国街道地址，如 '5500 Grand Lake Dr, San Antonio, TX 78244'。", "米国の住所（例: '5500 Grand Lake Dr, San Antonio, TX 78244'）。", "Endereço nos EUA, por exemplo '5500 Grand Lake Dr, San Antonio, TX 78244'.")),
    "city": (L("City", "城市", "市", "Cidade"),
             L("US city name; use with state.", "美国城市名，与 state 一起用。", "米国の市名。stateと併用。", "Nome da cidade nos EUA; use com state.")),
    "state": (L("State", "州", "州", "Estado"),
              L("Two-letter US state code, e.g. TX.", "两位美国州码，如 TX。", "2文字の米国州コード（例: TX）。", "Código de estado dos EUA com duas letras, por exemplo TX.")),
    "zip": (L("ZIP code", "邮编", "ZIPコード", "CEP (ZIP)"),
            L("Five-digit US ZIP code.", "五位美国邮编。", "5桁の米国ZIPコード。", "CEP (ZIP) dos EUA com cinco dígitos.")),
    "symbol": (L("Symbol", "代码", "銘柄コード", "Símbolo"),
               L("Ticker with exchange, e.g. AAPL:NASDAQ.", "带交易所的股票代码，如 AAPL:NASDAQ。", "取引所付きのティッカー（例: AAPL:NASDAQ）。", "Ticker com bolsa, por exemplo AAPL:NASDAQ.")),
}

# Which request fields each tool shows in Dify. A tool not listed here shows
# every field of its request schema. The API still accepts the fields left
# out; they are simply not offered to the model.
FIELDS = {
    "web_research": ["action", "provider", "query", "url", "country"],
    "company_intelligence": ["action", "provider", "domain", "country"],
    "people_search": ["action", "provider", "job_titles", "seniorities", "locations", "company_domain", "full_name", "email", "linkedin_url"],
    "seo_research": ["action", "provider", "keywords", "domain", "country"],
    "social_research": ["platform", "mode", "provider", "query", "handle", "url"],
    "market_data": ["action", "provider", "address", "city", "state", "zip", "symbol"],
}

LIST_NOTE = L("Comma-separated, up to {n}.", "逗号分隔，最多 {n} 个。", "カンマ区切り、最大{n}件。", "Separado por vírgula, até {n}.")

# ---------------------------------------------------------------- options
# Labels for enum values. A value with no entry gets the value itself.

OPTIONS = {
    "auto": L("Auto (Glasser picks)", "自动（由 Glasser 选择）", "自動（Glasserが選択）", "Automático (Glasser escolhe)"),
    "apollo": L("Apollo", "Apollo", "Apollo", "Apollo"), "pdl": L("People Data Labs", "People Data Labs", "People Data Labs", "People Data Labs"),
    "hunter": L("Hunter", "Hunter", "Hunter", "Hunter"), "prospeo": L("Prospeo", "Prospeo", "Prospeo", "Prospeo"),
    "leadmagic": L("LeadMagic", "LeadMagic", "LeadMagic", "LeadMagic"), "zoominfo": L("ZoomInfo", "ZoomInfo", "ZoomInfo", "ZoomInfo"),
    "predictleads": L("PredictLeads", "PredictLeads", "PredictLeads", "PredictLeads"), "builtwith": L("BuiltWith", "BuiltWith", "BuiltWith", "BuiltWith"),
    "dataforseo": L("DataForSEO", "DataForSEO", "DataForSEO", "DataForSEO"), "ahrefs": L("Ahrefs", "Ahrefs", "Ahrefs", "Ahrefs"),
    "semrush": L("Semrush", "Semrush", "Semrush", "Semrush"), "serpstat": L("Serpstat", "Serpstat", "Serpstat", "Serpstat"),
    "serper": L("Serper", "Serper", "Serper", "Serper"), "serpapi": L("SerpApi", "SerpApi", "SerpApi", "SerpApi"),
    "exa": L("Exa", "Exa", "Exa", "Exa"), "apify": L("Apify", "Apify", "Apify", "Apify"),
    "scrapecreators": L("ScrapeCreators", "ScrapeCreators", "ScrapeCreators", "ScrapeCreators"), "tikhub": L("TikHub", "TikHub", "TikHub", "TikHub"),
    "rentcast": L("RentCast", "RentCast", "RentCast", "RentCast"),
    # people_search
    "enrich": L("Enrich", "补全", "補完", "Enriquecer"),
    "find_email": L("Find work email", "查找工作邮箱", "仕事用メールを検索", "Encontrar e-mail de trabalho"),
    # company_intelligence
    "tech_stack": L("Technology stack", "技术栈", "技術スタック", "Stack de tecnologia"),
    "traffic": L("Website traffic", "网站流量", "サイトトラフィック", "Tráfego do site"),
    "competitors": L("Competitors", "竞争对手", "競合", "Concorrentes"),
    "funding": L("Funding rounds", "融资记录", "資金調達", "Rodadas de investimento"),
    "news": L("News", "新闻", "ニュース", "Notícias"),
    # seo_research
    "keyword_overview": L("Keyword metrics", "关键词指标", "キーワード指標", "Métricas de palavra-chave"),
    "keyword_ideas": L("Keyword ideas", "关键词拓展", "キーワード候補", "Ideias de palavras-chave"),
    "serp": L("Google results for a keyword", "关键词的 Google 结果", "キーワードのGoogle結果", "Resultados do Google para uma palavra-chave"),
    "domain_overview": L("Domain organic overview", "域名自然流量概览", "ドメインのオーガニック概要", "Visão geral orgânica do domínio"),
    "ranked_keywords": L("Keywords a domain ranks for", "域名排名关键词", "ドメインのランキングキーワード", "Palavras-chave em que o domínio rankeia"),
    "backlinks_overview": L("Backlink totals", "外链总览", "被リンク総計", "Totais de backlinks"),
    "backlinks": L("Backlinks list", "外链列表", "被リンク一覧", "Lista de backlinks"),
    "referring_domains": L("Referring domains", "引荐域名", "参照ドメイン", "Domínios de referência"),
    "domain_rating": L("Domain rating", "域名评分", "ドメインレーティング", "Domain Rating"),
    "organic_competitors": L("Organic search competitors", "自然搜索竞争对手", "オーガニック検索の競合", "Concorrentes na busca orgânica"),
    # web_research
    "search": L("Search", "搜索", "検索", "Buscar"),
    "places": L("Places / local businesses", "地点 / 本地商家", "場所・ローカルビジネス", "Lugares / negócios locais"),
    "scholar": L("Academic papers", "学术论文", "学術論文", "Artigos acadêmicos"),
    "shopping": L("Shopping", "商品", "ショッピング", "Compras"),
    "images": L("Images", "图片", "画像", "Imagens"),
    "videos": L("Videos", "视频", "動画", "Vídeos"),
    "answer": L("Answer a question from the web", "从网页回答问题", "ウェブから質問に回答", "Responder uma pergunta a partir da web"),
    "scrape": L("Read a web page", "读取网页", "ウェブページを読む", "Ler uma página web"),
    "similar": L("Pages similar to a URL", "与 URL 相似的页面", "URLに類似したページ", "Páginas semelhantes a uma URL"),
    # social_research
    "reddit": L("Reddit", "Reddit", "Reddit", "Reddit"), "x": L("X", "X", "X", "X"), "youtube": L("YouTube", "YouTube", "YouTube", "YouTube"),
    "tiktok": L("TikTok", "TikTok", "TikTok", "TikTok"), "instagram": L("Instagram", "Instagram", "Instagram", "Instagram"), "linkedin": L("LinkedIn", "LinkedIn", "LinkedIn", "LinkedIn"),
    "profile": L("Profile or channel", "主页或频道", "プロフィール/チャンネル", "Perfil ou canal"),
    "feed": L("Recent posts", "最近帖子", "最近の投稿", "Posts recentes"),
    "post": L("One post", "单条帖子", "1件の投稿", "Um post"),
    "find": L("Find social profiles", "查找社交账号", "SNSプロフィールを検索", "Encontrar perfis sociais"),
    # market_data
    "property_value": L("Property value estimate", "房产估值", "不動産価値の推定", "Estimativa de valor do imóvel"),
    "property_rent": L("Rent estimate", "租金估算", "家賃の推定", "Estimativa de aluguel"),
    "property_search": L("Property records", "房产记录", "不動産記録", "Registros de imóveis"),
    "listings_sale": L("For-sale listings", "在售房源", "売り出し物件", "Imóveis à venda"),
    "listings_rental": L("Rental listings", "出租房源", "賃貸物件", "Imóveis para alugar"),
    "market_stats": L("ZIP market statistics", "邮编市场统计", "ZIPコード市場統計", "Estatísticas de mercado por CEP"),
    "stock_quote": L("Stock quote", "股票行情", "株価", "Cotação de ação"),
}

# ------------------------------------------------------------- generation


def load_openapi(source: str) -> dict:
    if re.match(r"^https?://", source):
        with urllib.request.urlopen(source, timeout=30) as response:
            return json.load(response)
    return json.loads(Path(source).read_text(encoding="utf-8"))


def unwrap(prop: dict) -> tuple[dict, bool]:
    """Strip the `anyOf [X, null]` an optional field is encoded as."""
    if "anyOf" in prop:
        branches = [b for b in prop["anyOf"] if b.get("type") != "null"]
        if len(branches) == 1:
            return branches[0], True
    return prop, False


def default_of(schema: dict, name: str, tool: str) -> str | None:
    """The default value the contract states as 'Default <value>.' in the description."""
    match = re.match(r"^Default (\w+)\.", schema.get("description") or "")
    if not match:
        return None
    value = match.group(1)
    if value not in schema["enum"]:
        raise SystemExit(f"{tool}.{name}: default {value!r} is not one of {schema['enum']}")
    return value


def build_param(tool: str, name: str, prop: dict, required: bool) -> dict:
    schema, _nullable = unwrap(prop)
    key = f"{tool}.{name}" if f"{tool}.{name}" in PARAMS else name
    if key not in PARAMS:
        raise SystemExit(f"{tool}.{name}: no label in PARAMS; add one")
    label, human = PARAMS[key]
    llm = schema.get("description") or human["en_US"]
    param: dict = {"name": name, "type": "string", "required": required, "label": label, "human_description": human}

    if "enum" in schema:
        param["type"] = "select"
        param["options"] = [{"value": v, "label": OPTIONS.get(v, L(v, v, v, v))} for v in schema["enum"]]
        default = default_of(schema, name, tool)
        if default is not None:
            param["default"] = default
        elif name == "provider":
            param["default"] = "auto"
        if not schema.get("description"):
            llm = "One of: " + ", ".join(schema["enum"]) + "."
    elif schema.get("type") == "array":
        n = schema.get("maxItems", 20)
        human = {lang: text + ("" if lang in ("zh_Hans", "ja_JP") else " ") + LIST_NOTE[lang].format(n=n) for lang, text in human.items()}
        param["human_description"] = human
        llm = f"{llm} {LIST_NOTE['en_US'].format(n=n)}"
    elif schema.get("type") == "integer":
        param["type"] = "number"
        if "minimum" in schema:
            param["min"] = schema["minimum"]
        if "maximum" in schema:
            param["max"] = schema["maximum"]

    param["llm_description"] = llm
    param["form"] = "llm"
    return param


def build_tool(tool: str, op: dict) -> tuple[dict, dict]:
    """The Dify tool yaml and the runtime hints (list and integer fields)."""
    if tool not in TOOLS:
        raise SystemExit(f"{tool}: no copy in TOOLS; add one")
    schema = op["requestBody"]["content"]["application/json"]["schema"]
    required = set(schema.get("required") or [])
    shown = FIELDS.get(tool)
    if shown is not None:
        missing = [n for n in shown if n not in schema["properties"]]
        if missing:
            raise SystemExit(f"{tool}: FIELDS names {missing}, not in the request schema")
        if not required <= set(shown):
            raise SystemExit(f"{tool}: FIELDS leaves out required fields {sorted(required - set(shown))}")
    params = [
        build_param(tool, name, prop, name in required)
        for name, prop in schema["properties"].items()
        if shown is None or name in shown
    ]
    visible = {n: p for n, p in schema["properties"].items() if shown is None or n in shown}
    hints = {
        "lists": sorted(n for n, p in visible.items() if unwrap(p)[0].get("type") == "array"),
        "integers": sorted(n for n, p in visible.items() if unwrap(p)[0].get("type") == "integer"),
    }
    spec = TOOLS[tool]
    doc = {
        "identity": {"name": tool, "author": "glasser-ai", "label": spec["label"]},
        "description": {"human": spec["human"], "llm": spec["llm"]},
        "parameters": params,
        "extra": {"python": {"source": f"tools/{tool}.py"}},
    }
    return doc, hints


class Dumper(yaml.SafeDumper):
    pass


def _str(dumper, s):
    style = '"' if any(c in s for c in ":'\"#{}[]") else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", s, style=style)


Dumper.add_representer(str, _str)


def main(source: str) -> None:
    openapi = load_openapi(source)
    tools = {}
    for path, item in openapi["paths"].items():
        if path.startswith(PATH_PREFIX) and "post" in item:
            tools[path[len(PATH_PREFIX):]] = item["post"]
    if not tools:
        raise SystemExit(f"no {PATH_PREFIX}* operations in {source}")

    hints = {}
    for tool, op in tools.items():
        doc, hints[tool] = build_tool(tool, op)
        out = ROOT / "tools" / f"{tool}.yaml"
        out.write_text(yaml.dump(doc, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)} ({len(doc['parameters'])} parameters)")

    module = ROOT / "utils" / "gtm_schema.py"
    module.write_text(
        '"""Generated by scripts/gen_tools.py from the Glasser OpenAPI document. Do not edit.\n\n'
        "Which fields of each capability the API takes as arrays (the plugin splits a\n"
        'comma-separated string) and as integers (the plugin coerces the number).\n"""\n\n'
        f"SOLUTION = {SOLUTION!r}\n\n"
        f"CAPABILITIES = {json.dumps(sorted(tools))}\n\n"
        "LIST_FIELDS = {\n" + "".join(f"    {t!r}: {json.dumps(h['lists'])},\n" for t, h in sorted(hints.items())) + "}\n\n"
        "INT_FIELDS = {\n" + "".join(f"    {t!r}: {json.dumps(h['integers'])},\n" for t, h in sorted(hints.items())) + "}\n",
        encoding="utf-8",
    )
    print(f"wrote {module.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OPENAPI_URL)
