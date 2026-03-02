"""
Ticker database for autocomplete search (V2).

Contains ~350 Korean (KOSPI/KOSDAQ) and US (S&P500/NASDAQ/ETF) tickers
mapped to English and Korean company names separately.
Provides search_tickers() for querying by English name or ticker code.
"""

# {ticker_code: {"en": english_name, "ko": korean_name}}
TICKER_DB = {
    # ===== 한국 주요 종목 (KOSPI .KS / KOSDAQ .KQ) =====
    # KOSPI
    "005930.KS": {"en": "Samsung Electronics", "ko": "삼성전자"},
    "000660.KS": {"en": "SK Hynix", "ko": "SK하이닉스"},
    "373220.KS": {"en": "LG Energy Solution", "ko": "LG에너지솔루션"},
    "207940.KS": {"en": "Samsung Biologics", "ko": "삼성바이오로직스"},
    "005935.KS": {"en": "Samsung Electronics Pref", "ko": "삼성전자우"},
    "006400.KS": {"en": "Samsung SDI", "ko": "삼성SDI"},
    "051910.KS": {"en": "LG Chem", "ko": "LG화학"},
    "005380.KS": {"en": "Hyundai Motor", "ko": "현대차"},
    "000270.KS": {"en": "Kia", "ko": "기아"},
    "035420.KS": {"en": "NAVER", "ko": "네이버"},
    "035720.KS": {"en": "Kakao", "ko": "카카오"},
    "068270.KS": {"en": "Celltrion", "ko": "셀트리온"},
    "105560.KS": {"en": "KB Financial", "ko": "KB금융"},
    "055550.KS": {"en": "Shinhan Financial", "ko": "신한지주"},
    "012330.KS": {"en": "Hyundai Mobis", "ko": "현대모비스"},
    "066570.KS": {"en": "LG Electronics", "ko": "LG전자"},
    "003670.KS": {"en": "POSCO Future M", "ko": "포스코퓨처엠"},
    "028260.KS": {"en": "Samsung C&T", "ko": "삼성물산"},
    "096770.KS": {"en": "SK Innovation", "ko": "SK이노베이션"},
    "034730.KS": {"en": "SK Inc", "ko": "SK"},
    "003550.KS": {"en": "LG Corp", "ko": "LG"},
    "032830.KS": {"en": "Samsung Life Insurance", "ko": "삼성생명"},
    "086790.KS": {"en": "Hana Financial", "ko": "하나금융지주"},
    "030200.KS": {"en": "KT Corp", "ko": "KT"},
    "017670.KS": {"en": "SK Telecom", "ko": "SK텔레콤"},
    "316140.KS": {"en": "Woori Financial", "ko": "우리금융지주"},
    "033780.KS": {"en": "KT&G", "ko": "KT&G"},
    "009150.KS": {"en": "Samsung Electro-Mechanics", "ko": "삼성전기"},
    "011200.KS": {"en": "HMM", "ko": "HMM"},
    "034020.KS": {"en": "Doosan Enerbility", "ko": "두산에너빌리티"},
    "010130.KS": {"en": "Korea Zinc", "ko": "고려아연"},
    "047810.KS": {"en": "Korea Aerospace Industries", "ko": "한국항공우주산업"},
    "000810.KS": {"en": "Samsung Fire & Marine", "ko": "삼성화재"},
    "018260.KS": {"en": "Samsung SDS", "ko": "삼성에스디에스"},
    "024110.KS": {"en": "IBK Industrial Bank", "ko": "기업은행"},
    "015760.KS": {"en": "KEPCO", "ko": "한국전력"},
    "009540.KS": {"en": "HD Korea Shipbuilding", "ko": "한국조선해양"},
    "010950.KS": {"en": "S-Oil", "ko": "S-Oil"},
    "036570.KS": {"en": "NCSoft", "ko": "엔씨소프트"},
    "259960.KS": {"en": "Krafton", "ko": "크래프톤"},
    "011170.KS": {"en": "Lotte Chemical", "ko": "롯데케미칼"},
    "004020.KS": {"en": "Hyundai Steel", "ko": "현대제철"},
    "005490.KS": {"en": "POSCO Holdings", "ko": "POSCO홀딩스"},
    "326030.KS": {"en": "SK Biopharmaceuticals", "ko": "SK바이오팜"},
    "302440.KS": {"en": "SK Bioscience", "ko": "SK바이오사이언스"},
    "003490.KS": {"en": "Korean Air", "ko": "대한항공"},
    "090430.KS": {"en": "Amorepacific", "ko": "아모레퍼시픽"},
    "021240.KS": {"en": "Coway", "ko": "코웨이"},
    "011780.KS": {"en": "Kumho Petrochemical", "ko": "금호석유"},
    "000720.KS": {"en": "Hyundai E&C", "ko": "현대건설"},
    "006800.KS": {"en": "Mirae Asset Securities", "ko": "미래에셋증권"},
    "010140.KS": {"en": "Samsung Heavy Industries", "ko": "삼성중공업"},
    "004170.KS": {"en": "Shinsegae", "ko": "신세계"},
    "128940.KS": {"en": "Hanmi Pharm", "ko": "한미약품"},
    "180640.KS": {"en": "Hanjin Kal", "ko": "한진칼"},
    "035250.KS": {"en": "Kangwon Land", "ko": "강원랜드"},
    "012450.KS": {"en": "Hanwha Aerospace", "ko": "한화에어로스페이스"},
    "042700.KS": {"en": "Hanmi Semiconductor", "ko": "한미반도체"},
    "267260.KS": {"en": "HD Hyundai Electric", "ko": "HD현대일렉트릭"},
    "272210.KS": {"en": "Hanwha Systems", "ko": "한화시스템"},
    "009830.KS": {"en": "Hanwha Solutions", "ko": "한화솔루션"},
    "138040.KS": {"en": "Meritz Financial", "ko": "메리츠금융지주"},
    "352820.KS": {"en": "HYBE", "ko": "하이브"},
    "377300.KS": {"en": "Kakao Pay", "ko": "카카오페이"},
    "307950.KS": {"en": "Hyundai AutoEver", "ko": "현대오토에버"},
    "161390.KS": {"en": "Hankook Tire", "ko": "한국타이어"},
    "011790.KS": {"en": "SKC", "ko": "SKC"},
    "241560.KS": {"en": "Doosan Bobcat", "ko": "두산밥캣"},
    "078930.KS": {"en": "GS Corp", "ko": "GS"},
    "271560.KS": {"en": "Orion", "ko": "오리온"},
    "323410.KS": {"en": "Kakao Bank", "ko": "카카오뱅크"},
    "361610.KS": {"en": "SK IE Technology", "ko": "SK아이이테크놀로지"},
    "383220.KS": {"en": "F&F", "ko": "F&F"},
    "402340.KS": {"en": "SK Square", "ko": "SK스퀘어"},

    # KOSDAQ
    "247540.KQ": {"en": "Ecopro BM", "ko": "에코프로비엠"},
    "086520.KQ": {"en": "Ecopro", "ko": "에코프로"},
    "403870.KQ": {"en": "HPSP", "ko": "HPSP"},
    "196170.KQ": {"en": "Alteogen", "ko": "알테오젠"},
    "058470.KQ": {"en": "LEENO Industrial", "ko": "리노공업"},
    "041510.KQ": {"en": "SM Entertainment", "ko": "에스엠"},
    "263750.KQ": {"en": "Pearl Abyss", "ko": "펄어비스"},
    "293490.KQ": {"en": "Kakao Games", "ko": "카카오게임즈"},
    "068760.KQ": {"en": "Celltrion Pharm", "ko": "셀트리온제약"},
    "035900.KQ": {"en": "JYP Entertainment", "ko": "JYP엔터테인먼트"},
    "112040.KQ": {"en": "Wemade", "ko": "위메이드"},
    "357780.KQ": {"en": "Soulbrain", "ko": "솔브레인"},
    "240810.KQ": {"en": "Wonik IPS", "ko": "원익IPS"},
    "145020.KQ": {"en": "Hugel", "ko": "휴젤"},
    "036930.KQ": {"en": "Jusung Engineering", "ko": "주성엔지니어링"},
    "095340.KQ": {"en": "ISC", "ko": "ISC"},
    "039030.KQ": {"en": "EO Technics", "ko": "이오테크닉스"},
    "257720.KQ": {"en": "Silicon2", "ko": "실리콘투"},
    "328130.KQ": {"en": "Lunit", "ko": "루닛"},
    "078340.KQ": {"en": "Com2uS", "ko": "컴투스"},
    "060310.KQ": {"en": "3S", "ko": "쓰리에스"},

    # ===== 한국 ETF =====
    # KOSPI 200 / 주요 지수
    "069500.KS": {"en": "KODEX 200", "ko": "KODEX 200"},
    "102110.KS": {"en": "TIGER 200", "ko": "TIGER 200"},
    "148020.KS": {"en": "RISE 200", "ko": "RISE 200"},
    "069660.KS": {"en": "KIWOOM 200", "ko": "KIWOOM 200"},
    "152100.KS": {"en": "PLUS 200", "ko": "PLUS 200"},
    "278540.KS": {"en": "KODEX MSCI Korea TR", "ko": "KODEX MSCI Korea TR"},
    "310970.KS": {"en": "TIGER MSCI Korea TR", "ko": "TIGER MSCI Korea TR"},
    "229200.KS": {"en": "KODEX KOSDAQ150", "ko": "KODEX 코스닥150"},
    "232080.KS": {"en": "TIGER KOSDAQ150", "ko": "TIGER 코스닥150"},
    "139260.KS": {"en": "TIGER 200 IT", "ko": "TIGER 200 IT"},
    "227550.KS": {"en": "TIGER 200 Industrials", "ko": "TIGER 200 건설"},
    "251350.KS": {"en": "KODEX MSCI World", "ko": "KODEX MSCI World"},

    # 레버리지 / 인버스
    "122630.KS": {"en": "KODEX Leverage", "ko": "KODEX 레버리지"},
    "114800.KS": {"en": "KODEX Inverse", "ko": "KODEX 인버스"},
    "252670.KS": {"en": "KODEX 200 Futures Inverse 2X", "ko": "KODEX 200선물인버스2X"},
    "123320.KS": {"en": "TIGER 200 Leverage", "ko": "TIGER 레버리지"},
    "123310.KS": {"en": "TIGER 200 Inverse", "ko": "TIGER 200선물인버스"},
    "252710.KS": {"en": "TIGER 200 Futures Inverse 2X", "ko": "TIGER 200선물인버스2X"},
    "233740.KS": {"en": "KODEX KOSDAQ150 Leverage", "ko": "KODEX 코스닥150레버리지"},
    "251340.KS": {"en": "KODEX KOSDAQ150 Inverse", "ko": "KODEX 코스닥150인버스"},
    "250780.KS": {"en": "TIGER KOSDAQ150 Inverse", "ko": "TIGER 코스닥150인버스"},

    # 섹터 / 테마
    "091160.KS": {"en": "KODEX Semiconductor", "ko": "KODEX 반도체"},
    "091230.KS": {"en": "TIGER Semiconductor", "ko": "TIGER 반도체"},
    "396500.KS": {"en": "TIGER Fn Semiconductor TOP10", "ko": "TIGER Fn반도체TOP10"},
    "305720.KS": {"en": "KODEX Secondary Battery Industry", "ko": "KODEX 2차전지산업"},
    "305540.KS": {"en": "TIGER Secondary Battery", "ko": "TIGER 2차전지테마"},
    "465330.KS": {"en": "RISE Secondary Cell TOP10", "ko": "RISE 2차전지TOP10"},
    "244580.KS": {"en": "KODEX Bio", "ko": "KODEX 바이오"},
    "091170.KS": {"en": "KODEX Banks", "ko": "KODEX 은행"},
    "091180.KS": {"en": "KODEX Autos", "ko": "KODEX 자동차"},
    "091220.KS": {"en": "TIGER Banks", "ko": "TIGER 은행"},
    "117700.KS": {"en": "KODEX Construction", "ko": "KODEX 건설"},
    "117680.KS": {"en": "KODEX Steel", "ko": "KODEX 철강"},
    "140700.KS": {"en": "KODEX Insurance", "ko": "KODEX 보험"},
    "140710.KS": {"en": "KODEX Transportation", "ko": "KODEX 운송"},
    "157490.KS": {"en": "TIGER Software", "ko": "TIGER 소프트웨어"},
    "228790.KS": {"en": "TIGER Cosmetics", "ko": "TIGER 화장품"},
    "228800.KS": {"en": "TIGER Travel Leisure", "ko": "TIGER 여행레저"},
    "228810.KS": {"en": "TIGER Media Contents", "ko": "TIGER 미디어컨텐츠"},
    "329200.KS": {"en": "TIGER REITs Real Estate Infra", "ko": "TIGER 리츠부동산인프라"},
    "385510.KS": {"en": "KODEX Renewable Energy Active", "ko": "KODEX 신재생에너지액티브"},
    "385520.KS": {"en": "KODEX Autonomous Driving Active", "ko": "KODEX 자율주행액티브"},
    "371460.KS": {"en": "TIGER China Electric Vehicle", "ko": "TIGER 차이나전기차"},

    # 해외지수
    "360750.KS": {"en": "TIGER S&P500", "ko": "TIGER 미국S&P500"},
    "133690.KS": {"en": "TIGER NASDAQ100", "ko": "TIGER 미국나스닥100"},
    "379800.KS": {"en": "KODEX S&P500", "ko": "KODEX 미국S&P500"},
    "379810.KS": {"en": "KODEX US NASDAQ100", "ko": "KODEX 미국나스닥100"},
    "143850.KS": {"en": "TIGER S&P500 Futures(H)", "ko": "TIGER 미국S&P500선물(H)"},
    "448290.KS": {"en": "TIGER S&P500 TR(H)", "ko": "TIGER 미국S&P500(H)"},
    "304940.KS": {"en": "KODEX US NASDAQ100 Futures(H)", "ko": "KODEX 미국나스닥100선물(H)"},
    "448300.KS": {"en": "TIGER NASDAQ100(H)", "ko": "TIGER 미국나스닥100(H)"},
    "381170.KS": {"en": "TIGER US Tech TOP10 INDXX", "ko": "TIGER 미국테크TOP10"},
    "381180.KS": {"en": "TIGER US PHLX Semiconductor", "ko": "TIGER 미국필라델피아반도체나스닥"},
    "409820.KS": {"en": "KODEX US NASDAQ100 Leverage", "ko": "KODEX 미국나스닥100레버리지(합성H)"},
    "360200.KS": {"en": "ACE S&P500", "ko": "ACE 미국S&P500"},
    "367380.KS": {"en": "ACE US NASDAQ100", "ko": "ACE 미국나스닥100"},
    "368590.KS": {"en": "RISE US NASDAQ100", "ko": "RISE 미국나스닥100"},
    "465580.KS": {"en": "ACE US Big Tech TOP7 Plus", "ko": "ACE 미국빅테크TOP7Plus"},
    "195930.KS": {"en": "TIGER Euro Stoxx 50(H)", "ko": "TIGER 유로스톡스50(합성H)"},
    "192090.KS": {"en": "TIGER China A300", "ko": "TIGER 차이나CSI300"},
    "371160.KS": {"en": "TIGER China Hang Seng TECH", "ko": "TIGER 차이나항셍테크"},
    "241180.KS": {"en": "TIGER Nikkei225", "ko": "TIGER 일본니케이225"},
    "453810.KS": {"en": "KODEX India Nifty50", "ko": "KODEX 인도Nifty50"},
    "236350.KS": {"en": "TIGER India Leverage(Synth)", "ko": "TIGER 인도레버리지(합성)"},
    "189400.KS": {"en": "PLUS MSCI AC World(H)", "ko": "PLUS 글로벌(합성H)"},
    "352560.KS": {"en": "KODEX US Real Estate(H)", "ko": "KODEX 미국부동산리츠(H)"},
    "453630.KS": {"en": "KODEX S&P500 Consumer Staples", "ko": "KODEX S&P500필수소비재"},
    "453640.KS": {"en": "KODEX S&P500 Health Care", "ko": "KODEX S&P500헬스케어"},
    "453650.KS": {"en": "KODEX S&P500 Financial", "ko": "KODEX S&P500금융"},
    "456250.KS": {"en": "KODEX Europe Luxury TOP10", "ko": "KODEX 유럽럭셔리TOP10"},

    # 채권 / 금 / 원자재
    "114260.KS": {"en": "KODEX Treasury Bond 3Y", "ko": "KODEX 국고채3년"},
    "148070.KS": {"en": "KIWOOM Treasury Bond 10Y", "ko": "KIWOOM 국고채10년"},
    "152380.KS": {"en": "KODEX Treasury Bond 10Y", "ko": "KODEX 국고채10년"},
    "302190.KS": {"en": "TIGER KTB 3-10Y", "ko": "TIGER 중장기국채"},
    "439870.KS": {"en": "KODEX Treasury Bond 30Y Active", "ko": "KODEX 국고채30년액티브"},
    "385560.KS": {"en": "RISE Treasury Bond 30Y Enhanced", "ko": "RISE 국고채30년"},
    "153130.KS": {"en": "KODEX Short Term Bond", "ko": "KODEX 단기채권"},
    "272560.KS": {"en": "RISE Short KTB Active", "ko": "RISE 단기국채액티브"},
    "305080.KS": {"en": "TIGER 10Y US T-Note Futures", "ko": "TIGER 미국채10년선물"},
    "308620.KS": {"en": "KODEX US T-Note Futures", "ko": "KODEX 미국채선물"},
    "304660.KS": {"en": "KODEX Ultra T-Bond Futures(H)", "ko": "KODEX 미국채울트라30년선물(H)"},
    "357870.KS": {"en": "TIGER CD Rate(Synth)", "ko": "TIGER CD금리투자(합성)"},
    "459580.KS": {"en": "KODEX CD Rate Active(Synth)", "ko": "KODEX CD금리액티브(합성)"},
    "449170.KS": {"en": "TIGER KOFR Active(Synth)", "ko": "TIGER KOFR금리액티브(합성)"},
    "455030.KS": {"en": "KODEX USD SOFR Active(Synth)", "ko": "KODEX 미국달러SOFR금리액티브(합성)"},
    "132030.KS": {"en": "KODEX Gold Futures(H)", "ko": "KODEX 골드선물(H)"},
    "319640.KS": {"en": "TIGER Gold Futures(H)", "ko": "TIGER 골드선물(H)"},
    "411060.KS": {"en": "ACE KRX Physical Gold", "ko": "ACE KRX금현물"},
    "130680.KS": {"en": "TIGER WTI Futures", "ko": "TIGER 원유선물Enhanced(H)"},
    "261220.KS": {"en": "KODEX WTI Oil Futures(H)", "ko": "KODEX WTI원유선물(H)"},
    "271050.KS": {"en": "KODEX WTI Futures Inverse(H)", "ko": "KODEX WTI원유선물인버스(H)"},
    "217770.KS": {"en": "TIGER WTI Inverse(H)", "ko": "TIGER 원유선물인버스(H)"},

    # 배당 / 커버드콜 / 스마트베타
    "211560.KS": {"en": "TIGER Dividend Growth", "ko": "TIGER 배당성장"},
    "161510.KS": {"en": "PLUS High Dividend", "ko": "PLUS 고배당주"},
    "266160.KS": {"en": "RISE High Dividend", "ko": "RISE 고배당"},
    "174350.KS": {"en": "TIGER Low Volatility", "ko": "TIGER 로우볼"},
    "458730.KS": {"en": "TIGER US Dividend Equity", "ko": "TIGER 미국배당다우존스"},
    "441640.KS": {"en": "KODEX US Dividend Premium Active", "ko": "KODEX 미국배당프리미엄액티브"},
    "441680.KS": {"en": "TIGER NASDAQ100 Covered Call", "ko": "TIGER 나스닥100커버드콜(합성)"},
    "472150.KS": {"en": "TIGER Dividend Covered Call Active", "ko": "TIGER 배당프리미엄액티브"},
    "476550.KS": {"en": "TIGER 30Y UST Covered Call", "ko": "TIGER 미국30년국채프리미엄액티브(H)"},

    # ===== 미국 주요 종목 (S&P500, NASDAQ, ETF) =====
    # Big Tech / Mega Cap
    "AAPL":  {"en": "Apple", "ko": "애플"},
    "MSFT":  {"en": "Microsoft", "ko": "마이크로소프트"},
    "GOOGL": {"en": "Alphabet (Google)", "ko": "구글"},
    "GOOG":  {"en": "Alphabet Class C", "ko": "구글C"},
    "AMZN":  {"en": "Amazon", "ko": "아마존"},
    "NVDA":  {"en": "NVIDIA", "ko": "엔비디아"},
    "META":  {"en": "Meta Platforms", "ko": "메타"},
    "TSLA":  {"en": "Tesla", "ko": "테슬라"},
    "BRK-B": {"en": "Berkshire Hathaway B", "ko": "버크셔해서웨이"},
    "TSM":   {"en": "TSMC", "ko": "대만반도체"},

    # Tech / Software
    "AVGO": {"en": "Broadcom", "ko": "브로드컴"},
    "ORCL": {"en": "Oracle", "ko": "오라클"},
    "CRM":  {"en": "Salesforce", "ko": "세일즈포스"},
    "ADBE": {"en": "Adobe", "ko": "어도비"},
    "AMD":  {"en": "AMD", "ko": "AMD"},
    "INTC": {"en": "Intel", "ko": "인텔"},
    "QCOM": {"en": "Qualcomm", "ko": "퀄컴"},
    "TXN":  {"en": "Texas Instruments", "ko": "텍사스인스트루먼트"},
    "MU":   {"en": "Micron", "ko": "마이크론"},
    "AMAT": {"en": "Applied Materials", "ko": "어플라이드머티리얼즈"},
    "LRCX": {"en": "Lam Research", "ko": "램리서치"},
    "KLAC": {"en": "KLA Corp", "ko": "KLA"},
    "SNPS": {"en": "Synopsys", "ko": "시놉시스"},
    "CDNS": {"en": "Cadence Design", "ko": "케이던스"},
    "NOW":  {"en": "ServiceNow", "ko": "서비스나우"},
    "PANW": {"en": "Palo Alto Networks", "ko": "팔로알토"},
    "CRWD": {"en": "CrowdStrike", "ko": "크라우드스트라이크"},
    "SHOP": {"en": "Shopify", "ko": "쇼피파이"},
    "SQ":   {"en": "Block (Square)", "ko": "블록"},
    "PLTR": {"en": "Palantir", "ko": "팔란티어"},
    "SNOW": {"en": "Snowflake", "ko": "스노우플레이크"},
    "NET":  {"en": "Cloudflare", "ko": "클라우드플레어"},
    "DDOG": {"en": "Datadog", "ko": "데이터독"},
    "MRVL": {"en": "Marvell", "ko": "마벨"},
    "ARM":  {"en": "Arm Holdings", "ko": "ARM"},
    "SMCI": {"en": "Super Micro Computer", "ko": "슈퍼마이크로"},

    # Communication / Media
    "NFLX":  {"en": "Netflix", "ko": "넷플릭스"},
    "DIS":   {"en": "Walt Disney", "ko": "디즈니"},
    "CMCSA": {"en": "Comcast", "ko": "컴캐스트"},
    "TMUS":  {"en": "T-Mobile", "ko": "T모바일"},
    "VZ":    {"en": "Verizon", "ko": "버라이즌"},
    "T":     {"en": "AT&T", "ko": "AT&T"},
    "SPOT":  {"en": "Spotify", "ko": "스포티파이"},

    # Finance
    "JPM":  {"en": "JPMorgan Chase", "ko": "JP모건"},
    "V":    {"en": "Visa", "ko": "비자"},
    "MA":   {"en": "Mastercard", "ko": "마스터카드"},
    "BAC":  {"en": "Bank of America", "ko": "뱅크오브아메리카"},
    "WFC":  {"en": "Wells Fargo", "ko": "웰스파고"},
    "GS":   {"en": "Goldman Sachs", "ko": "골드만삭스"},
    "MS":   {"en": "Morgan Stanley", "ko": "모건스탠리"},
    "AXP":  {"en": "American Express", "ko": "아메리칸익스프레스"},
    "BLK":  {"en": "BlackRock", "ko": "블랙록"},
    "PYPL": {"en": "PayPal", "ko": "페이팔"},
    "COIN": {"en": "Coinbase", "ko": "코인베이스"},

    # Healthcare / Pharma
    "UNH":  {"en": "UnitedHealth", "ko": "유나이티드헬스"},
    "JNJ":  {"en": "Johnson & Johnson", "ko": "존슨앤드존슨"},
    "LLY":  {"en": "Eli Lilly", "ko": "일라이릴리"},
    "PFE":  {"en": "Pfizer", "ko": "화이자"},
    "ABBV": {"en": "AbbVie", "ko": "애브비"},
    "MRK":  {"en": "Merck", "ko": "머크"},
    "TMO":  {"en": "Thermo Fisher", "ko": "써모피셔"},
    "ABT":  {"en": "Abbott Labs", "ko": "애보트"},
    "ISRG": {"en": "Intuitive Surgical", "ko": "인튜이티브서지컬"},
    "MRNA": {"en": "Moderna", "ko": "모더나"},

    # Consumer
    "WMT":  {"en": "Walmart", "ko": "월마트"},
    "PG":   {"en": "Procter & Gamble", "ko": "P&G"},
    "KO":   {"en": "Coca-Cola", "ko": "코카콜라"},
    "PEP":  {"en": "PepsiCo", "ko": "펩시코"},
    "COST": {"en": "Costco", "ko": "코스트코"},
    "HD":   {"en": "Home Depot", "ko": "홈디포"},
    "MCD":  {"en": "McDonald's", "ko": "맥도날드"},
    "NKE":  {"en": "Nike", "ko": "나이키"},
    "SBUX": {"en": "Starbucks", "ko": "스타벅스"},
    "TGT":  {"en": "Target", "ko": "타겟"},
    "LOW":  {"en": "Lowe's", "ko": "로우스"},

    # Industrial / Energy
    "XOM": {"en": "ExxonMobil", "ko": "엑슨모빌"},
    "CVX": {"en": "Chevron", "ko": "쉐브론"},
    "LMT": {"en": "Lockheed Martin", "ko": "록히드마틴"},
    "RTX": {"en": "RTX (Raytheon)", "ko": "레이시온"},
    "BA":  {"en": "Boeing", "ko": "보잉"},
    "CAT": {"en": "Caterpillar", "ko": "캐터필러"},
    "GE":  {"en": "GE Aerospace", "ko": "GE에어로스페이스"},
    "UPS": {"en": "UPS", "ko": "UPS"},
    "DE":  {"en": "John Deere", "ko": "디어"},
    "HON": {"en": "Honeywell", "ko": "허니웰"},

    # ETF — 주요 인덱스
    "SPY":  {"en": "SPDR S&P 500 ETF", "ko": "S&P500 ETF"},
    "VOO":  {"en": "Vanguard S&P 500 ETF", "ko": "뱅가드 S&P500"},
    "IVV":  {"en": "iShares Core S&P 500", "ko": "iShares S&P500"},
    "QQQ":  {"en": "Invesco Nasdaq-100 ETF", "ko": "나스닥100 ETF"},
    "DIA":  {"en": "SPDR Dow Jones ETF", "ko": "다우존스 ETF"},
    "VTI":  {"en": "Vanguard Total Stock Market", "ko": "전체주식시장"},
    "VT":   {"en": "Vanguard Total World Stock", "ko": "전세계주식"},
    "VEA":  {"en": "Vanguard FTSE Developed Markets", "ko": "선진국"},
    "VWO":  {"en": "Vanguard FTSE Emerging Markets", "ko": "신흥국"},
    "IWM":  {"en": "iShares Russell 2000", "ko": "러셀2000 소형주"},

    # ETF — 섹터 / 테마
    "XLK":  {"en": "Technology Select Sector", "ko": "기술섹터 ETF"},
    "XLF":  {"en": "Financial Select Sector", "ko": "금융섹터 ETF"},
    "XLE":  {"en": "Energy Select Sector", "ko": "에너지섹터 ETF"},
    "XLV":  {"en": "Health Care Select Sector", "ko": "헬스케어 ETF"},
    "ARKK": {"en": "ARK Innovation ETF", "ko": "ARK혁신 ETF"},
    "SOXX": {"en": "iShares Semiconductor ETF", "ko": "반도체 ETF"},
    "SMH":  {"en": "VanEck Semiconductor ETF", "ko": "반도체 ETF"},

    # ETF — 채권 / 기타
    "BND":  {"en": "Vanguard Total Bond Market", "ko": "채권 ETF"},
    "TLT":  {"en": "iShares 20+ Year Treasury", "ko": "장기국채 ETF"},
    "AGG":  {"en": "iShares Core US Aggregate Bond", "ko": "종합채권"},
    "GLD":  {"en": "SPDR Gold Shares", "ko": "금 ETF"},
    "SLV":  {"en": "iShares Silver Trust", "ko": "은 ETF"},
    "VNQ":  {"en": "Vanguard Real Estate REIT ETF", "ko": "부동산"},
    "SCHD": {"en": "Schwab US Dividend Equity", "ko": "배당 ETF"},
    "JEPI": {"en": "JPMorgan Equity Premium Income", "ko": "프리미엄인컴"},
}


def search_tickers(query, max_results=15):
    """Search TICKER_DB by English name or ticker code.

    Args:
        query: Search string (English name or ticker code, case-insensitive).
        max_results: Maximum number of results to return.

    Returns:
        List of (ticker_code, en_name, ko_name) tuples sorted by relevance.
        Exact ticker match → English name prefix → English name contains.
    """
    if not query or not query.strip():
        return []

    q = query.strip()
    q_upper = q.upper()
    q_lower = q.lower()

    exact_matches = []
    prefix_matches = []
    contains_matches = []

    for code, info in TICKER_DB.items():
        code_upper = code.upper()
        en_lower = info["en"].lower()

        # Exact ticker match
        if code_upper == q_upper:
            exact_matches.append((code, info["en"], info["ko"]))
        # Ticker prefix match
        elif code_upper.startswith(q_upper):
            prefix_matches.append((code, info["en"], info["ko"]))
        # English name prefix match
        elif en_lower.startswith(q_lower):
            prefix_matches.append((code, info["en"], info["ko"]))
        # English name contains query
        elif q_lower in en_lower:
            contains_matches.append((code, info["en"], info["ko"]))

    exact_matches.sort(key=lambda x: x[0])
    prefix_matches.sort(key=lambda x: x[0])
    contains_matches.sort(key=lambda x: x[0])

    results = exact_matches + prefix_matches + contains_matches
    return results[:max_results]


def resolve_ticker(query):
    """Convert input string to ticker code with en/ko names.

    Args:
        query: Ticker code or English company name.

    Returns:
        (ticker_code, en_name, ko_name) tuple, or None if no match found.
    """
    if not query or not query.strip():
        return None

    q = query.strip()
    q_upper = q.upper()

    # Direct ticker match
    if q_upper in TICKER_DB:
        info = TICKER_DB[q_upper]
        return (q_upper, info["en"], info["ko"])

    # Case-insensitive ticker match (e.g., "aapl" → "AAPL")
    for code, info in TICKER_DB.items():
        if code.upper() == q_upper:
            return (code, info["en"], info["ko"])

    # Fuzzy search fallback
    results = search_tickers(q, max_results=1)
    if results:
        return results[0]

    return None
