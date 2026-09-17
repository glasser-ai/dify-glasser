"""Generate tools/<capability>.yaml from one spec: labels in four languages,
the action and provider selects from utils.routes, and the shared parameters."""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import routes  # noqa: E402

L = lambda en, zh, ja, pt: {"en_US": en, "zh_Hans": zh, "ja_JP": ja, "pt_BR": pt}  # noqa: E731

PROVIDER_LABELS = {
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
}

# Shared parameter definitions; each tool lists the ones it uses.
P = {
    "query": ("string", L("Query", "查询", "クエリ", "Consulta"), L("Search phrase or question.", "搜索词或问题。", "検索語または質問。", "Termo de busca ou pergunta.")),
    "url": ("string", L("URL", "URL", "URL", "URL"), L("A full http(s) URL.", "完整的 http(s) URL。", "完全なhttp(s) URL。", "Uma URL http(s) completa.")),
    "domain": ("string", L("Domain", "域名", "ドメイン", "Domínio"), L("A company website domain, e.g. stripe.com.", "公司网站域名，如 stripe.com。", "企業サイトのドメイン（例: stripe.com）。", "O domínio do site da empresa, por exemplo stripe.com.")),
    "keywords": ("string", L("Keywords", "关键词", "キーワード", "Palavras-chave"), L("One or more keywords, comma-separated.", "一个或多个关键词，逗号分隔。", "1つ以上のキーワード、カンマ区切り。", "Uma ou mais palavras-chave, separadas por vírgula.")),
    "country": ("string", L("Country", "国家", "国", "País"), L("Two-letter country code, e.g. us, gb, de (default us).", "两位国家代码，如 us、gb、de（默认 us）。", "2文字の国コード（例: us, gb, de、デフォルトus）。", "Código de país de duas letras, por exemplo us, gb, de (padrão us).")),
    "language": ("string", L("Language", "语言", "言語", "Idioma"), L("Two-letter language code for the results, e.g. en, de.", "结果语言的两位代码，如 en、de。", "結果の言語コード（例: en, de）。", "Código de idioma de duas letras para os resultados, por exemplo en, de.")),
    "limit": ("number", L("Limit", "数量", "件数", "Limite"), L("How many rows to return. Keep it small: the charge may depend on it.", "返回行数。保持小量：扣费可能与它相关。", "返す行数。少なめに：課金額が依存する場合があります。", "Quantas linhas retornar. Mantenha baixo: a cobrança pode depender disso.")),
    "job_titles": ("string", L("Job titles", "职位", "役職", "Cargos"), L("Comma-separated job titles, e.g. 'CTO, VP Engineering'.", "职位列表，逗号分隔，如 'CTO, VP Engineering'。", "役職のカンマ区切りリスト（例: 'CTO, VP Engineering'）。", "Cargos separados por vírgula, por exemplo 'CTO, VP Engineering'.")),
    "seniorities": ("string", L("Seniorities", "级别", "役職レベル", "Senioridades"), L("Comma-separated seniority levels, e.g. 'c_suite, vp, director' (search with apollo).", "级别列表，逗号分隔，如 'c_suite, vp, director'（apollo 的 search 用）。", "役職レベルのカンマ区切り（例: 'c_suite, vp, director'、apolloのsearch用）。", "Níveis de senioridade separados por vírgula, por exemplo 'c_suite, vp, director' (search com apollo).")),
    "locations": ("string", L("Locations", "地区", "所在地", "Localizações"), L("Comma-separated cities, states or countries.", "城市、州或国家，逗号分隔。", "都市、州、国のカンマ区切り。", "Cidades, estados ou países separados por vírgula.")),
    "company_domain": ("string", L("Company domain", "公司域名", "企業ドメイン", "Domínio da empresa"), L("The employer's website domain, e.g. stripe.com.", "雇主的网站域名，如 stripe.com。", "雇用主のサイトのドメイン（例: stripe.com）。", "O domínio do site do empregador, por exemplo stripe.com.")),
    "company_name": ("string", L("Company name", "公司名称", "企業名", "Nome da empresa"), L("The employer's name, when the domain is unknown.", "雇主名称，域名未知时使用。", "雇用主の名前（ドメイン不明時）。", "O nome do empregador, quando o domínio é desconhecido.")),
    "keywords_people": ("string", L("Keywords", "关键词", "キーワード", "Palavras-chave"), L("Free-text keywords for people search (apollo).", "人物搜索的自由关键词（apollo）。", "人物検索の自由キーワード（apollo）。", "Palavras-chave livres para busca de pessoas (apollo).")),
    "full_name": ("string", L("Full name", "全名", "氏名", "Nome completo"), L("The person's full name, e.g. 'Patrick Collison'.", "人物全名，如 'Patrick Collison'。", "人物の氏名（例: 'Patrick Collison'）。", "O nome completo da pessoa, por exemplo 'Patrick Collison'.")),
    "email": ("string", L("Email", "邮箱", "メール", "E-mail"), L("The person's email address.", "人物的邮箱地址。", "人物のメールアドレス。", "O endereço de e-mail da pessoa.")),
    "linkedin_url": ("string", L("LinkedIn URL", "LinkedIn 链接", "LinkedIn URL", "URL do LinkedIn"), L("The person's LinkedIn profile URL.", "人物的 LinkedIn 个人主页链接。", "人物のLinkedInプロフィールURL。", "A URL do perfil do LinkedIn da pessoa.")),
    "handle": ("string", L("Handle", "账号", "ハンドル", "Handle"), L("A username or handle without @, or a subreddit name.", "用户名或账号（不带 @），或 subreddit 名称。", "@なしのユーザー名またはハンドル、あるいはsubreddit名。", "Um nome de usuário ou handle sem @, ou o nome de um subreddit.")),
    "platform": ("string", L("Platform", "平台", "プラットフォーム", "Plataforma"), L("For find_profiles: instagram, tiktok, youtube, x, twitter or facebook.", "find_profiles 用：instagram、tiktok、youtube、x、twitter 或 facebook。", "find_profiles用: instagram, tiktok, youtube, x, twitter, facebook。", "Para find_profiles: instagram, tiktok, youtube, x, twitter ou facebook.")),
}

ACTIONS = {
    "people_search": {
        "search": L("Search people", "搜索人物", "人物を検索", "Buscar pessoas"),
        "enrich": L("Enrich one person", "补全一个人", "1人を補完", "Enriquecer uma pessoa"),
        "find_email": L("Find work email", "查找工作邮箱", "仕事用メールを検索", "Encontrar e-mail de trabalho"),
    },
    "company_intelligence": {
        "enrich": L("Company profile", "公司档案", "企業プロフィール", "Perfil da empresa"),
        "tech_stack": L("Technology stack", "技术栈", "技術スタック", "Stack de tecnologia"),
        "traffic": L("Website traffic", "网站流量", "サイトトラフィック", "Tráfego do site"),
        "competitors": L("Competitors", "竞争对手", "競合", "Concorrentes"),
        "funding": L("Funding rounds", "融资记录", "資金調達", "Rodadas de investimento"),
        "news": L("Company news", "公司新闻", "企業ニュース", "Notícias da empresa"),
    },
    "seo_research": {
        "keyword_overview": L("Keyword metrics", "关键词指标", "キーワード指標", "Métricas de palavra-chave"),
        "keyword_ideas": L("Keyword ideas", "关键词拓展", "キーワード候補", "Ideias de palavras-chave"),
        "domain_overview": L("Domain organic overview", "域名自然流量概览", "ドメインのオーガニック概要", "Visão geral orgânica do domínio"),
        "ranked_keywords": L("Keywords a domain ranks for", "域名排名关键词", "ドメインのランキングキーワード", "Palavras-chave em que o domínio rankeia"),
        "backlinks_overview": L("Backlink totals", "外链总览", "被リンク総計", "Totais de backlinks"),
        "backlinks": L("Backlinks list", "外链列表", "被リンク一覧", "Lista de backlinks"),
        "referring_domains": L("Referring domains", "引荐域名", "参照ドメイン", "Domínios de referência"),
        "domain_rating": L("Domain rating", "域名评分", "ドメインレーティング", "Domain Rating"),
        "serp": L("Google results for a keyword", "关键词的 Google 结果", "キーワードのGoogle結果", "Resultados do Google para uma palavra-chave"),
    },
    "web_research": {
        "search": L("Web search", "网页搜索", "ウェブ検索", "Busca na web"),
        "news": L("News search", "新闻搜索", "ニュース検索", "Busca de notícias"),
        "scrape": L("Read a web page", "读取网页", "ウェブページを読む", "Ler uma página web"),
        "places": L("Places / local businesses", "地点 / 本地商家", "場所・ローカルビジネス", "Lugares / negócios locais"),
        "scholar": L("Academic papers", "学术论文", "学術論文", "Artigos acadêmicos"),
        "shopping": L("Shopping", "商品", "ショッピング", "Compras"),
        "images": L("Images", "图片", "画像", "Imagens"),
        "videos": L("Videos", "视频", "動画", "Vídeos"),
        "answer": L("Answer a question from the web", "从网页回答问题", "ウェブから質問に回答", "Responder uma pergunta a partir da web"),
        "similar": L("Pages similar to a URL", "与 URL 相似的页面", "URLに類似したページ", "Páginas semelhantes a uma URL"),
    },
    "social_research": {
        "reddit_search": L("Reddit search", "Reddit 搜索", "Reddit検索", "Busca no Reddit"),
        "reddit_subreddit": L("Subreddit posts", "Subreddit 帖子", "Subredditの投稿", "Posts de um subreddit"),
        "x_user_tweets": L("X user's tweets", "X 用户推文", "Xユーザーの投稿", "Tweets de um usuário do X"),
        "x_tweet": L("X tweet details", "X 推文详情", "X投稿の詳細", "Detalhes de um tweet do X"),
        "youtube_search": L("YouTube search", "YouTube 搜索", "YouTube検索", "Busca no YouTube"),
        "youtube_channel": L("YouTube channel videos", "YouTube 频道视频", "YouTubeチャンネルの動画", "Vídeos de um canal do YouTube"),
        "tiktok_search": L("TikTok search", "TikTok 搜索", "TikTok検索", "Busca no TikTok"),
        "instagram_profile": L("Instagram profile", "Instagram 主页", "Instagramプロフィール", "Perfil do Instagram"),
        "linkedin_posts": L("LinkedIn posts search", "LinkedIn 帖子搜索", "LinkedIn投稿検索", "Busca de posts no LinkedIn"),
        "linkedin_profile": L("LinkedIn profile", "LinkedIn 个人主页", "LinkedInプロフィール", "Perfil do LinkedIn"),
        "linkedin_company": L("LinkedIn company page", "LinkedIn 公司主页", "LinkedIn企業ページ", "Página de empresa no LinkedIn"),
        "find_profiles": L("Find social profiles", "查找社交账号", "SNSプロフィールを検索", "Encontrar perfis sociais"),
    },
}

TOOLS = {
    "people_search": dict(
        label=L("Find People", "找人", "人物検索", "Encontrar pessoas"),
        human=L("Find B2B people and decision makers, enrich one person, or find a work email. Apollo, People Data Labs, Hunter, Prospeo, LeadMagic and ZoomInfo behind one Key; provider=auto picks for you.",
                "查找 B2B 人物和决策者、补全一个人、或查找工作邮箱。一个 Key 背后是 Apollo、People Data Labs、Hunter、Prospeo、LeadMagic、ZoomInfo；provider=auto 自动选择。",
                "B2Bの人物や意思決定者を検索、1人を補完、仕事用メールを検索。Apollo、People Data Labs、Hunter、Prospeo、LeadMagic、ZoomInfoを1つのKeyで。provider=autoで自動選択。",
                "Encontre pessoas B2B e decisores, enriqueça uma pessoa ou encontre um e-mail de trabalho. Apollo, People Data Labs, Hunter, Prospeo, LeadMagic e ZoomInfo com uma única Key; provider=auto escolhe por você."),
        llm="Find B2B people. action 'search': people matching job_titles, seniorities, locations, company_domain or keywords (any combination; apollo search is free, results carry name, title and employer). action 'enrich': one known person's profile and contact data from linkedin_url, email, or full_name plus company_domain. action 'find_email': the work email of full_name at company_domain. provider 'auto' picks apollo for search and enrich, hunter for find_email; name a provider only when the user asks for one. Each call is one paid run; report the charge and the run URL.",
        params=["job_titles", "seniorities", "locations", "company_domain", "company_name", "keywords_people", "full_name", "email", "linkedin_url", "limit"],
    ),
    "company_intelligence": dict(
        label=L("Company Intelligence", "公司情报", "企業インテリジェンス", "Inteligência de empresas"),
        human=L("Everything about one company from its domain: profile and firmographics, technology stack, website traffic, competitors, funding rounds, news. Apollo, PDL, Hunter, PredictLeads, BuiltWith, DataForSEO, Ahrefs and more behind one Key.",
                "按域名了解一家公司：档案与画像、技术栈、网站流量、竞争对手、融资、新闻。一个 Key 背后是 Apollo、PDL、Hunter、PredictLeads、BuiltWith、DataForSEO、Ahrefs 等。",
                "ドメインから企業のすべてを: プロフィール、技術スタック、サイトトラフィック、競合、資金調達、ニュース。Apollo、PDL、Hunter、PredictLeads、BuiltWith、DataForSEO、Ahrefsなどを1つのKeyで。",
                "Tudo sobre uma empresa a partir do domínio: perfil e firmografia, stack de tecnologia, tráfego do site, concorrentes, rodadas de investimento, notícias. Apollo, PDL, Hunter, PredictLeads, BuiltWith, DataForSEO, Ahrefs e mais com uma única Key."),
        llm="Company intelligence for one domain. action 'enrich': industry, size, revenue, HQ, funding summary. 'tech_stack': technologies the site runs. 'traffic': estimated organic traffic (dataforseo) or Similarweb-style visits (apify). 'competitors': domains competing for the same keywords, or similar companies (predictleads). 'funding': funding rounds with dates and investors. 'news': classified company events (predictleads) or Google News (serper). domain is always required. provider 'auto' picks the default per action; name one only when the user asks. Each call is one paid run; report the charge and the run URL.",
        params=["domain", "country", "limit", "query"],
    ),
    "seo_research": dict(
        label=L("SEO Research", "SEO 研究", "SEOリサーチ", "Pesquisa de SEO"),
        human=L("Keyword volume and difficulty, keyword ideas, a domain's organic traffic and ranking keywords, backlinks and referring domains, domain rating, Google results. Semrush, DataForSEO, Ahrefs and Serpstat behind one Key.",
                "关键词量与难度、关键词拓展、域名自然流量与排名关键词、外链与引荐域名、域名评分、Google 结果。一个 Key 背后是 Semrush、DataForSEO、Ahrefs、Serpstat。",
                "キーワードのボリュームと難易度、キーワード候補、ドメインのオーガニックトラフィックとランキングキーワード、被リンクと参照ドメイン、ドメインレーティング、Google結果。Semrush、DataForSEO、Ahrefs、Serpstatを1つのKeyで。",
                "Volume e dificuldade de palavras-chave, ideias de palavras-chave, tráfego orgânico e palavras-chave de um domínio, backlinks e domínios de referência, domain rating, resultados do Google. Semrush, DataForSEO, Ahrefs e Serpstat com uma única Key."),
        llm="SEO data. Keyword actions take keywords (comma-separated): 'keyword_overview' (volume, difficulty, CPC), 'keyword_ideas' (related terms), 'serp' (Google organic results for the first keyword). Domain actions take domain: 'domain_overview' (organic traffic and keyword count), 'ranked_keywords', 'backlinks_overview' (totals), 'backlinks' (rows), 'referring_domains', 'domain_rating' (Ahrefs DR, $0.0005). country is a two-letter code, default us. provider 'auto' picks the cheapest good source per action (semrush for one keyword, serpstat for several, dataforseo for domains); name a provider only when the user asks. Each call is one paid run; report the charge and the run URL.",
        params=["keywords", "domain", "country", "limit"],
    ),
    "web_research": dict(
        label=L("Web Research", "网页研究", "ウェブリサーチ", "Pesquisa na web"),
        human=L("Google web, news, places, scholar, shopping, image and video search, reading a web page, neural search and question answering. Serper, SerpApi and Exa behind one Key.",
                "Google 网页、新闻、地点、学术、商品、图片、视频搜索，读取网页，语义搜索与问答。一个 Key 背后是 Serper、SerpApi、Exa。",
                "Googleのウェブ、ニュース、場所、学術、ショッピング、画像、動画検索、ウェブページの読み取り、ニューラル検索と質問応答。Serper、SerpApi、Exaを1つのKeyで。",
                "Busca web, notícias, lugares, acadêmica, compras, imagens e vídeos do Google, leitura de páginas web, busca neural e resposta a perguntas. Serper, SerpApi e Exa com uma única Key."),
        llm="Live web data. Query actions take query: 'search' (Google organic results), 'news', 'places' (local businesses; put the area in the query), 'scholar', 'shopping', 'images', 'videos', 'answer' (a written answer with cited sources, exa). URL actions take url: 'scrape' (readable content and Markdown of one page), 'similar' (pages like this one, exa). provider 'auto' picks serper for Google-style actions and exa for answer and similar; 'exa' on search does neural search by meaning. Each call is one paid run, typically $0.001 to $0.015; report the charge and the run URL.",
        params=["query", "url", "country", "language", "limit"],
    ),
    "social_research": dict(
        label=L("Social Research", "社交研究", "ソーシャルリサーチ", "Pesquisa social"),
        human=L("Reddit, X, YouTube, TikTok, Instagram and LinkedIn: search posts, read a profile or channel, find someone's social accounts. ScrapeCreators, Apify and TikHub behind one Key.",
                "Reddit、X、YouTube、TikTok、Instagram、LinkedIn：搜索帖子、读取主页或频道、查找某人的社交账号。一个 Key 背后是 ScrapeCreators、Apify、TikHub。",
                "Reddit、X、YouTube、TikTok、Instagram、LinkedIn: 投稿の検索、プロフィールやチャンネルの取得、SNSアカウントの検索。ScrapeCreators、Apify、TikHubを1つのKeyで。",
                "Reddit, X, YouTube, TikTok, Instagram e LinkedIn: buscar posts, ler um perfil ou canal, encontrar as contas sociais de alguém. ScrapeCreators, Apify e TikHub com uma única Key."),
        llm="Public social data, read-only. Query actions take query: 'reddit_search', 'youtube_search', 'tiktok_search', 'linkedin_posts'. Handle actions take handle (no @; a subreddit name for reddit_subreddit): 'reddit_subreddit', 'x_user_tweets', 'youtube_channel', 'instagram_profile', 'find_profiles' (also needs platform). URL actions take url: 'x_tweet', 'linkedin_profile', 'linkedin_company'. provider 'auto' is scrapecreators (about $0.002 per call, sync); apify alternatives are async and priced per result. Each call is one paid run; report the charge and the run URL.",
        params=["query", "handle", "url", "platform", "limit"],
    ),
}


def param(name, ptype, label, desc, extra=None):
    d = {"name": name, "type": ptype, "required": False, "label": label, "human_description": desc, "llm_description": desc["en_US"], "form": "llm"}
    if extra:
        d.update(extra)
    return d


def build(tool, spec):
    actions = ACTIONS[tool]
    action_param = {
        "name": "action", "type": "select", "required": True, "default": next(iter(actions)),
        "options": [{"value": a, "label": lbl} for a, lbl in actions.items()],
        "label": L("Action", "操作", "アクション", "Ação"),
        "human_description": L("What to do; see the tool description.", "要做的事；见工具说明。", "実行内容。ツールの説明を参照。", "O que fazer; veja a descrição da ferramenta."),
        "llm_description": "One of: " + ", ".join(actions) + ".",
        "form": "llm",
    }
    providers = routes.providers_for(tool)
    provider_param = {
        "name": "provider", "type": "select", "required": False, "default": "auto",
        "options": [{"value": p, "label": PROVIDER_LABELS[p]} for p in providers],
        "label": L("Provider", "数据来源", "プロバイダー", "Provider"),
        "human_description": L("Which data provider to use. Auto lets Glasser pick a good default for the action.", "使用哪家数据提供方。auto 由 Glasser 为该操作选择默认来源。", "使用するデータプロバイダー。autoならGlasserがアクションに応じて選択。", "Qual provedor de dados usar. Auto deixa o Glasser escolher um bom padrão para a ação."),
        "llm_description": "Data provider: auto (default, recommended) or one of " + ", ".join(providers[1:]) + ". Name one only when the user asks for that vendor.",
        "form": "llm",
    }
    params = [action_param, provider_param]
    for name in spec["params"]:
        ptype, label, desc = P[name]
        real = "keywords" if name == "keywords_people" else name
        extra = {"min": 1} if ptype == "number" else None
        params.append(param(real, ptype, label, desc, extra))
    return {
        "identity": {"name": tool, "author": "glasser-ai", "label": spec["label"]},
        "description": {"human": spec["human"], "llm": spec["llm"]},
        "parameters": params,
        "extra": {"python": {"source": f"tools/{tool}.py"}},
    }


class D(yaml.SafeDumper):
    pass


def _str(dumper, s):
    style = '"' if any(c in s for c in ":'\"#{}[]") else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", s, style=style)


D.add_representer(str, _str)

root = Path(__file__).resolve().parents[1]
for tool, spec in TOOLS.items():
    out = root / "tools" / f"{tool}.yaml"
    with open(out, "w", encoding="utf-8") as f:
        yaml.dump(build(tool, spec), f, Dumper=D, sort_keys=False, allow_unicode=True, width=10000)
    print("wrote", out.name)
