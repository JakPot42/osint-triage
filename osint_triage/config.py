"""Configuration: foreign-language sources, analyst interest areas, priority tiers."""
from pathlib import Path

# ── framing note ────────────────────────────────────────────────────────────────
FRAMING_NOTE = (
    "INSTITUTIONAL/MEDIA LEVEL ONLY — public foreign-language news sources, "
    "same posture as SENTINEL's existing adversary-source monitoring. "
    "Not surveillance of individuals."
)

# ── Claude model ─────────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# ── database path ────────────────────────────────────────────────────────────────
DB_PATH = str(Path.home() / ".osint_triage" / "triage.db")

# ── ingestion limits ─────────────────────────────────────────────────────────────
MAX_ITEMS_PER_FEED = 25
MAX_EXTRACT_PER_RUN = 20

# ── foreign-language RSS sources ─────────────────────────────────────────────────
# (name, url, language, outlet_type)
FOREIGN_SOURCES = [
    # Russian-language adversary/state media
    ("TASS Russian",     "https://tass.ru/rss/v2.xml",                                        "Russian",  "state_media"),
    ("RT Russian",       "https://russian.rt.com/rss",                                        "Russian",  "adversary"),
    ("Sputnik Russian",  "https://sputnik.by/export/rss2/world/index.xml",                    "Russian",  "adversary"),
    # Chinese-language state media
    ("Global Times CN",  "https://www.globaltimes.cn/rss/china.xml",                          "Chinese",  "state_media"),
    ("Xinhua Chinese",   "http://www.xinhuanet.com/rss/news.xml",                             "Chinese",  "state_media"),
    # Arabic-language adversary/state media
    ("RT Arabic",        "https://arabic.rt.com/rss/",                                        "Arabic",   "adversary"),
    ("Sputnik Arabic",   "https://arabic.sputniknews.com/export/rss2/archive/index.xml",      "Arabic",   "adversary"),
    # Spanish-language (Latin American narrative ops)
    ("Sputnik Spanish",  "https://sputnikmundo.com/export/rss2/archive/index.xml",            "Spanish",  "adversary"),
    ("HispanTV",         "https://www.hispantv.com/rss",                                      "Spanish",  "adversary"),
    # Persian-language
    ("IRNA Persian",     "https://www.irna.ir/rss",                                           "Persian",  "state_media"),
]

# ── analyst interest areas ────────────────────────────────────────────────────────
# weight: per-keyword hit contribution to priority score
INTEREST_AREAS: dict[str, dict] = {
    "Nuclear/WMD": {
        "keywords": [
            "nuclear", "warhead", "icbm", "ballistic missile", "deterrence",
            "plutonium", "enrichment", "wmd", "hypersonic", "yield",
        ],
        "weight": 25,
    },
    "Military Operations": {
        "keywords": [
            "military", "troops", "offensive", "combat", "weapons", "missile",
            "drone", "naval", "air force", "ammunition", "frontline", "deployment",
            "invasion", "strike", "battalion",
        ],
        "weight": 15,
    },
    "Cyber Operations": {
        "keywords": [
            "cyber", "hack", "breach", "infrastructure attack", "malware",
            "ransomware", "espionage", "intrusion", "zero-day", "apt",
        ],
        "weight": 18,
    },
    "Technology Transfer": {
        "keywords": [
            "semiconductor", "chips", "quantum", "artificial intelligence",
            "technology transfer", "dual-use", "export controls", "microelectronics",
            "precision manufacturing", "advanced manufacturing",
        ],
        "weight": 20,
    },
    "Taiwan/South China Sea": {
        "keywords": [
            "taiwan", "south china sea", "taiwan strait", "pla", "reunification",
            "independence", "scs", "dprk", "korean peninsula",
        ],
        "weight": 20,
    },
    "Ukraine/NATO": {
        "keywords": [
            "ukraine", "nato", "kyiv", "donbas", "crimea", "zelensky",
            "escalation", "article 5", "eastern flank",
        ],
        "weight": 15,
    },
    "Middle East": {
        "keywords": [
            "gaza", "israel", "iran", "hamas", "hezbollah", "yemen",
            "houthi", "lebanon", "nuclear program", "iaea", "strait of hormuz",
        ],
        "weight": 15,
    },
    "Sanctions/Trade": {
        "keywords": [
            "sanctions", "export controls", "tariffs", "embargo",
            "trade restriction", "secondary sanctions", "asset freeze",
        ],
        "weight": 10,
    },
    "Diplomacy": {
        "keywords": [
            "summit", "treaty", "bilateral", "ceasefire", "negotiations",
            "agreement", "memorandum", "communique", "foreign minister",
        ],
        "weight": 8,
    },
}

# ── valid Claude topic labels ─────────────────────────────────────────────────────
VALID_TOPICS = list(INTEREST_AREAS.keys()) + ["Domestic Politics", "Other"]

# ── priority tiers ────────────────────────────────────────────────────────────────
PRIORITY_TIERS = [
    ("CRITICAL", 75),
    ("HIGH",     50),
    ("MEDIUM",   25),
    ("LOW",       0),
]

TIER_COLORS = {
    "CRITICAL": "bold red",
    "HIGH":     "bold yellow",
    "MEDIUM":   "cyan",
    "LOW":      "dim",
}

# ── demo seed data ────────────────────────────────────────────────────────────────
# Pre-baked items with pre-baked extractions so `demo` needs no API key.
# Titles/bodies are realistic examples of the TYPE of content such a tool
# would process — these are illustrative, NOT real current intelligence.
DEMO_SEEDS = [
    {
        "source_name": "TASS Russian",
        "language": "Russian",
        "outlet": "state_media",
        "url": "https://tass.ru/demo/001",
        "title_original": "Россия успешно испытала новую межконтинентальную баллистическую ракету",
        "body_original": (
            "Министерство обороны России сообщило об успешном испытании новой "
            "межконтинентальной баллистической ракеты класса «Сармат». "
            "Испытание прошло на полигоне Плесецк и подтвердило расчётные характеристики изделия. "
            "Дальность поражения составляет более 18 000 километров. "
            "Официальный представитель заявил, что ракета обеспечивает гарантированное ядерное сдерживание."
        ),
        "extraction": {
            "language": "Russian",
            "translation": (
                "Russia Successfully Tests New ICBM. Russia's Ministry of Defense announced "
                "a successful test of the new Sarmat-class intercontinental ballistic missile "
                "at the Plesetsk test site. The weapon has a reported range exceeding 18,000 km "
                "and is described as providing 'guaranteed nuclear deterrence'."
            ),
            "claims": [
                "Russia's Sarmat ICBM successfully tested at Plesetsk cosmodrome",
                "Reported range exceeds 18,000 kilometers",
                "MoD states the test confirmed design specifications",
            ],
            "entities": {
                "persons": [],
                "organizations": ["Russian Ministry of Defense", "Plesetsk Cosmodrome"],
                "locations": ["Plesetsk", "Russia"],
            },
            "topic": "Nuclear/WMD",
            "topic_tags": ["icbm", "nuclear", "ballistic missile", "deterrence"],
            "sensitivity": "CRITICAL",
        },
    },
    {
        "source_name": "Global Times CN",
        "language": "Chinese",
        "outlet": "state_media",
        "url": "https://www.globaltimes.cn/demo/002",
        "title_original": "解放军在台湾海峡部署核潜艇举行大规模演习",
        "body_original": (
            "解放军海军在台湾海峡举行大规模军事演习，据报道部署了配备核武器的弹道导弹核潜艇。"
            "此次演习被描述为对台湾当局最新分裂主义声明的反应。"
            "国防部发言人表示，这是对台湾独立势力的严重警告。"
            "演习包括两栖登陆演练、空中突击和海上封锁模拟。"
        ),
        "extraction": {
            "language": "Chinese",
            "translation": (
                "PLA Deploys Nuclear Submarines in Large-Scale Taiwan Strait Exercise. "
                "The PLA Navy conducted large-scale exercises in the Taiwan Strait, reportedly "
                "including nuclear-armed ballistic missile submarines. The exercises were framed "
                "as a response to recent statements by Taiwan's leadership. MoD spokesperson "
                "described them as a 'serious warning' against independence forces. Drills included "
                "amphibious landing rehearsals, air assault, and simulated naval blockade."
            ),
            "claims": [
                "PLA Navy deployed nuclear ballistic missile submarines in Taiwan Strait exercises",
                "Exercises included simulated amphibious landing and naval blockade",
                "MoD framed exercises as response to Taiwan separatist statements",
            ],
            "entities": {
                "persons": [],
                "organizations": ["PLA Navy", "Chinese Ministry of National Defense"],
                "locations": ["Taiwan Strait", "Taiwan", "China"],
            },
            "topic": "Taiwan/South China Sea",
            "topic_tags": ["taiwan", "nuclear", "pla", "naval", "ballistic missile"],
            "sensitivity": "CRITICAL",
        },
    },
    {
        "source_name": "RT Arabic",
        "language": "Arabic",
        "outlet": "adversary",
        "url": "https://arabic.rt.com/demo/003",
        "title_original": "إيران تعلن تخصيب اليورانيوم بنسبة 84% في منشأة فوردو",
        "body_original": (
            "أعلنت إيران أنها رفعت مستوى تخصيب اليورانيوم إلى 84% في منشأة فوردو تحت الأرض، "
            "وهو ما يقترب من مستوى الأسلحة البالغ 90%. "
            "قال الممثل الإيراني لدى الوكالة الدولية للطاقة الذرية إن ذلك جاء رداً على "
            "العقوبات الغربية المتصاعدة. الوكالة الدولية للطاقة الذرية طلبت توضيحات فورية."
        ),
        "extraction": {
            "language": "Arabic",
            "translation": (
                "Iran Announces 84% Uranium Enrichment at Fordow Facility. Iran has raised "
                "uranium enrichment levels to 84% at the underground Fordow facility, approaching "
                "the 90% weapons-grade threshold. Iran's representative to the IAEA stated this "
                "is a response to escalating Western sanctions. The IAEA has requested immediate "
                "clarification."
            ),
            "claims": [
                "Iran has enriched uranium to 84% at Fordow, near weapons-grade 90%",
                "Iran frames the move as retaliation for Western sanctions",
                "IAEA has formally requested clarification",
            ],
            "entities": {
                "persons": [],
                "organizations": ["IAEA", "Iranian Atomic Energy Organization"],
                "locations": ["Fordow", "Iran"],
            },
            "topic": "Nuclear/WMD",
            "topic_tags": ["nuclear", "enrichment", "iran", "iaea", "middle east"],
            "sensitivity": "CRITICAL",
        },
    },
    {
        "source_name": "RT Russian",
        "language": "Russian",
        "outlet": "adversary",
        "url": "https://russian.rt.com/demo/004",
        "title_original": "ФСБ: западные хакеры атаковали энергетическую инфраструктуру России",
        "body_original": (
            "Федеральная служба безопасности России объявила о раскрытии крупной кибератаки "
            "на объекты энергетической инфраструктуры страны. "
            "По данным ФСБ, атака была проведена с использованием вредоносного ПО типа APT, "
            "аналогичного образцам, ранее связанным с западными спецслужбами. "
            "Пострадали несколько региональных энергосистем на Урале."
        ),
        "extraction": {
            "language": "Russian",
            "translation": (
                "FSB Claims Western Hackers Attacked Russian Energy Infrastructure. Russia's FSB "
                "announced it uncovered a major cyber attack against Russian energy grid facilities. "
                "The FSB attributes the attack to APT-style malware linked to Western intelligence "
                "services. Several regional power systems in the Ural region were reportedly affected. "
                "(Note: attribution claims are FSB's own — not independently verified.)"
            ),
            "claims": [
                "FSB claims Western-linked APT malware attacked Russian energy infrastructure",
                "Several Ural region power systems were reportedly affected",
                "FSB attributes attack to Western intelligence services",
            ],
            "entities": {
                "persons": [],
                "organizations": ["FSB", "Russian Federal Security Service"],
                "locations": ["Ural", "Russia"],
            },
            "topic": "Cyber Operations",
            "topic_tags": ["cyber", "hack", "infrastructure attack", "apt", "espionage"],
            "sensitivity": "HIGH",
        },
    },
    {
        "source_name": "Xinhua Chinese",
        "language": "Chinese",
        "outlet": "state_media",
        "url": "https://www.xinhuanet.com/demo/005",
        "title_original": "中芯国际宣布突破5纳米制程工艺，挑战美国芯片封锁",
        "body_original": (
            "中芯国际集成电路制造有限公司宣布成功开发5纳米制程芯片工艺，"
            "此举被认为是对美国出口管制的重大突破。"
            "该公司表示新工艺已实现小批量量产，客户包括国内军民两用电子产品制造商。"
            "商务部表示将继续推动半导体自主化。"
        ),
        "extraction": {
            "language": "Chinese",
            "translation": (
                "SMIC Announces 5nm Process Breakthrough Challenging US Chip Blockade. "
                "Semiconductor Manufacturing International Corporation (SMIC) announced successful "
                "development of 5nm chip manufacturing processes, framed as a major breakthrough "
                "against US export controls. The company states limited-volume production is "
                "underway for domestic dual-use electronics manufacturers. China's Commerce "
                "Ministry pledged continued semiconductor self-sufficiency push."
            ),
            "claims": [
                "SMIC claims successful 5nm chip process development",
                "Limited-volume production reportedly underway for dual-use manufacturers",
                "China frames development as counter to US export controls",
            ],
            "entities": {
                "persons": [],
                "organizations": ["SMIC", "Chinese Ministry of Commerce"],
                "locations": ["China"],
            },
            "topic": "Technology Transfer",
            "topic_tags": ["semiconductor", "chips", "export controls", "dual-use"],
            "sensitivity": "HIGH",
        },
    },
    {
        "source_name": "Sputnik Russian",
        "language": "Russian",
        "outlet": "adversary",
        "url": "https://sputnik.by/demo/006",
        "title_original": "Россия и Китай подписали соглашение о поставках газа на 30 лет",
        "body_original": (
            "Россия и Китай подписали долгосрочное соглашение о поставках природного газа "
            "сроком на 30 лет. Стоимость контракта оценивается в 400 миллиардов долларов. "
            "Соглашение предусматривает строительство нового трубопровода через Монголию. "
            "Аналитики рассматривают сделку как способ обхода западных санкций."
        ),
        "extraction": {
            "language": "Russian",
            "translation": (
                "Russia and China Sign 30-Year Natural Gas Supply Agreement. Russia and China "
                "signed a long-term 30-year natural gas supply contract valued at approximately "
                "$400 billion. The agreement includes construction of a new pipeline through "
                "Mongolia. Analysts describe the deal as a mechanism to bypass Western sanctions."
            ),
            "claims": [
                "Russia-China sign 30-year gas supply deal worth ~$400 billion",
                "Deal includes new pipeline construction through Mongolia",
                "Analysts characterize deal as sanctions-circumvention mechanism",
            ],
            "entities": {
                "persons": [],
                "organizations": [],
                "locations": ["Russia", "China", "Mongolia"],
            },
            "topic": "Sanctions/Trade",
            "topic_tags": ["sanctions", "trade restriction", "bilateral", "energy"],
            "sensitivity": "MEDIUM",
        },
    },
    {
        "source_name": "Sputnik Arabic",
        "language": "Arabic",
        "outlet": "adversary",
        "url": "https://arabic.sputniknews.com/demo/007",
        "title_original": "المملكة العربية السعودية توسع شراكتها الدفاعية مع الصين",
        "body_original": (
            "أعلنت المملكة العربية السعودية عن توسيع شراكتها الدفاعية مع الصين، "
            "وتشمل الاتفاقية نقل تكنولوجيا الطائرات المسيّرة وتدريب الكوادر العسكرية. "
            "يرى المحللون أن الصفقة تشير إلى تراجع الاعتماد على الشركاء الغربيين. "
            "وزير الخارجية الصيني أكد الالتزام بالشراكة الاستراتيجية المشتركة."
        ),
        "extraction": {
            "language": "Arabic",
            "translation": (
                "Saudi Arabia Expands Defense Partnership with China. Saudi Arabia announced "
                "expansion of its defense partnership with China, including drone technology "
                "transfer and military training cooperation. Analysts view the deal as signaling "
                "reduced reliance on Western defense partners. China's Foreign Minister affirmed "
                "commitment to the joint strategic partnership."
            ),
            "claims": [
                "Saudi Arabia-China defense deal includes drone technology transfer",
                "Agreement covers military training cooperation",
                "Analysts frame deal as Saudi pivot away from Western defense partners",
            ],
            "entities": {
                "persons": [],
                "organizations": [],
                "locations": ["Saudi Arabia", "China", "Middle East"],
            },
            "topic": "Diplomacy",
            "topic_tags": ["bilateral", "military", "technology transfer", "middle east"],
            "sensitivity": "MEDIUM",
        },
    },
    {
        "source_name": "Sputnik Spanish",
        "language": "Spanish",
        "outlet": "adversary",
        "url": "https://sputnikmundo.com/demo/008",
        "title_original": "Rusia alerta sobre escalada de la OTAN en el este de Europa",
        "body_original": (
            "El Ministerio de Relaciones Exteriores de Rusia advirtió que la ampliación de la "
            "presencia de la OTAN en Europa del Este representa una amenaza directa para la "
            "seguridad nacional rusa. El portavoz señaló que Rusia se reserva el derecho a "
            "tomar medidas de respuesta simétricas. Se mencionaron los nuevos despliegues "
            "de la OTAN en los países bálticos como motivo de especial preocupación."
        ),
        "extraction": {
            "language": "Spanish",
            "translation": (
                "Russia Warns of NATO Escalation in Eastern Europe. Russia's Foreign Ministry "
                "warned that NATO's expanding presence in Eastern Europe constitutes a direct "
                "threat to Russian national security. The spokesperson stated Russia reserves the "
                "right to take 'symmetric response measures'. New NATO deployments in Baltic "
                "states were cited as a particular concern."
            ),
            "claims": [
                "Russia's MFA characterizes NATO Eastern European presence as national security threat",
                "Russia states it reserves the right to symmetric response measures",
                "Baltic state NATO deployments cited as specific concern",
            ],
            "entities": {
                "persons": [],
                "organizations": ["Russian Ministry of Foreign Affairs", "NATO"],
                "locations": ["Eastern Europe", "Baltic States", "Russia"],
            },
            "topic": "Ukraine/NATO",
            "topic_tags": ["nato", "ukraine", "escalation", "eastern flank"],
            "sensitivity": "MEDIUM",
        },
    },
    {
        "source_name": "TASS Russian",
        "language": "Russian",
        "outlet": "state_media",
        "url": "https://tass.ru/demo/009",
        "title_original": "Правительство России утвердило федеральный бюджет на 2027 год",
        "body_original": (
            "Правительство Российской Федерации утвердило проект федерального бюджета на "
            "2027 год. Расходы составят 35 триллионов рублей, доходы — 32 триллиона. "
            "Дефицит бюджета планируется покрыть за счёт Фонда национального благосостояния. "
            "Рост ВВП прогнозируется на уровне 2,1%."
        ),
        "extraction": {
            "language": "Russian",
            "translation": (
                "Russia Approves 2027 Federal Budget. The Russian government approved the "
                "2027 federal budget draft. Expenditures total 35 trillion rubles against "
                "32 trillion in revenue, with the deficit to be covered by the National "
                "Wealth Fund. GDP growth is forecast at 2.1%."
            ),
            "claims": [
                "Russia's 2027 budget sets spending at 35 trillion rubles",
                "Budget deficit to be covered by National Wealth Fund",
                "Official GDP growth forecast set at 2.1%",
            ],
            "entities": {
                "persons": [],
                "organizations": ["Government of the Russian Federation"],
                "locations": ["Russia"],
            },
            "topic": "Domestic Politics",
            "topic_tags": ["budget", "domestic", "economy"],
            "sensitivity": "LOW",
        },
    },
]
