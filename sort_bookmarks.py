#!/usr/bin/env python3
"""
Sort ALL bookmarks in the file into the correct folder categories.
Parses a Netscape bookmark HTML file, classifies every bookmark
by URL domain and title keywords, and overwrites the file with sorted results.

This does a FULL re-sort: every bookmark is scored against every folder,
and placed in the highest-scoring one. Bookmarks below the minimum threshold
go to "Other".
"""

import re
import html
from collections import defaultdict, OrderedDict
from urllib.parse import urlparse

INPUT_FILE = "/mnt/g/BookMarkManagement/favorites_3_17_26_cleaned.html"
OUTPUT_FILE = "/mnt/g/BookMarkManagement/favorites_3_17_26_cleaned.html"

MIN_SCORE_THRESHOLD = 2.5

# ============================================================
# FOLDER PROFILES
# ============================================================
# "strong_keywords" = multi-word or very specific (matched via substring)
# "keywords" = words needing word-boundary matching
# "title_only" = only match in the title text
# "domains" = exact domain matches (highest confidence)
# Each keyword match in title = +3, in url = +1.5
# Each strong_keyword in title = +4, in url = +2
# Each domain match = +8
# Each title_only match = +3

FOLDER_PROFILES = {
    "Archery": {
        "strong_keywords": ["archery", "bowhunt", "bow hunt", "bow hunting",
                            "usarchery", "bowhunter", "nasp"],
        "keywords": ["quiver", "crossbow", "broadhead", "fletching"],
        "domains": ["usarchery.org", "lhyarchery.com", "stlbowhunters.com",
                     "archerytalk.com", "lancasterarchery.com", "naspschools.org"],
    },
    "Banks & Credit Cards": {
        "strong_keywords": ["credit card", "credit union", "savings account",
                            "checking account", "credit score", "debit card",
                            "online banking", "mobile banking", "simmons bank",
                            "farmers state bank"],
        "keywords": [],
        "title_only": ["bank"],
        "domains": ["myfsb.bank", "chase.com", "bankofamerica.com", "wellsfargo.com",
                     "capitalone.com", "creditkarma.com", "discover.com",
                     "simmons.bank", "simmonsbank.com", "clickbank.com"],
    },
    "BookKeeping": {
        "strong_keywords": ["bookkeeping", "accounting", "quickbooks", "chart of accounts",
                            "depreciation", "amortization", "accounts payable",
                            "accounts receivable", "balance sheet", "profit and loss",
                            "general ledger", "waveapps", "double entry",
                            "plaid demo", "plaid pricing", "affiliate marketing",
                            "offervault"],
        "keywords": ["invoicing", "payroll", "bookkeeper"],
        "domains": ["waveapps.com", "quickbooks.intuit.com", "plaid.com", "xero.com",
                     "freshbooks.com", "offervault.com"],
    },
    "Bowling": {
        "strong_keywords": ["bowling ball", "bowling alley", "bowling league",
                            "bowling shoe", "bowling technique", "bowling drill",
                            "bowling university", "bowling products", "bowlingball",
                            "bowlversity", "pyramid bowling", "pba tour",
                            "bowling database", "brown bowl", "bowwwl"],
        "keywords": ["bowling", "bowler", "usbc"],
        "domains": ["bowlingball.com", "bowl.com", "pyramidbowling.com", "usbc.org",
                     "pba.com", "bowwwl.com"],
    },
    "Business": {
        "strong_keywords": ["entrepreneur", "startup weekend", "business strategy",
                            "business plan", "venture capital", "growth hacking",
                            "business model", "pitch deck", "seed funding",
                            "salesforce clone", "marketing tool",
                            "100 startup", "strategyzer", "founderpal",
                            "build your data team", "kalzumeus",
                            "grocery shopping for others",
                            "sponsorship opportunit", "affiliate program",
                            "alternative investment", "instagram follower",
                            "linkedin post", "career brand",
                            "seo beginner", "digital path to business",
                            "great game of business", "product hunt",
                            "agency owner", "course creation",
                            "online store solution"],
        "keywords": ["entrepreneurship", "ecommerce"],
        "title_only": ["startup", "affiliate"],
        "domains": ["entrepreneur.com", "inc.com", "hbr.org", "sba.gov",
                     "strategyzer.com", "founderpal.com", "leanstack.com",
                     "producthunt.com", "skool.com"],
    },
    "BusinessTools": {
        "strong_keywords": ["project management", "email marketing", "web hosting",
                            "zoho crm", "trello", "mailchimp", "mailgun", "sendgrid",
                            "landing page", "domain name", "newsletter subscriber",
                            "automate email", "bitnami", "website builder",
                            "namechk", "namecheckr", "slack workspace",
                            "host website", "vps host", "centos server",
                            "teamspeak server", "digitalocean", "vultr",
                            "swap on ubuntu", "composer on ubuntu",
                            "spectre fleet slack", "slyce slack",
                            "azure foundry", "microsoft azure dashboard",
                            "perpendulum", "calendar table",
                            "email test", "loomly", "reseller hosting",
                            "name generator", "password generator",
                            "business name generator", "domain generator",
                            "file converter", "online converter",
                            "screen recorder", "animation maker",
                            "ai prompt", "prompt framework",
                            "funnel marketing", "clickfunnels",
                            "appsumo", "software deal"],
        "keywords": ["saas", "trello", "asana", "zapier", "zoho"],
        "domains": ["mailchimp.com", "hubspot.com", "trello.com", "asana.com",
                     "zoom.us", "notion.so", "airtable.com", "zapier.com",
                     "mailgun.com", "sendgrid.com", "ionos.com", "siteground.com",
                     "bluehost.com", "godaddy.com", "namecheap.com", "cloudflare.com",
                     "namechk.com", "namecheckr.com", "zoho.com", "site123.com",
                     "loomly.com", "digitalocean.com", "vultr.com", "servermom.org",
                     "vpstutorial.com", "bitnami.com", "azure.com",
                     "portal.azure.com"],
    },
    "DataScienceTools": {
        "strong_keywords": ["data science", "pandas documentation", "jupyter notebook",
                            "data visualization", "data analysis", "data mining",
                            "scikit-learn", "matplotlib", "10 minutes to pandas",
                            "rocket data science", "python bootcamp"],
        "keywords": ["kaggle", "jupyter"],
        "domains": ["kaggle.com", "pandas.pydata.org", "jupyter.org", "scipy.org",
                     "scikit-learn.org", "rocketdatascience.org",
                     "nbviewer.jupyter.org"],
    },
    "Deep Learning": {
        "strong_keywords": ["deep learning", "neural network", "tensorflow",
                            "pytorch", "machine learning", "natural language processing",
                            "computer vision", "reinforcement learning",
                            "deep learning rig", "i am trask"],
        "keywords": ["tensorflow", "pytorch", "keras"],
        "domains": ["tensorflow.org", "pytorch.org", "keras.io",
                     "huggingface.co", "deeplearning.ai", "fast.ai",
                     "iamtrask.github.io"],
    },
    "Development": {
        "strong_keywords": ["software development", "web development",
                            "rest api", "angularjs", "angular js", "spring mvc",
                            "electron app", "visual studio code", "oracle jdeveloper",
                            "crud using", "api documentation", "data generator",
                            "mockaroo", "ui kit", "rapid application",
                            "python framework", "scrum methodology",
                            "agile development", "random data generator",
                            "bootstrap 5", "material design", "dreamfactory",
                            "curl rest api", "github.com", "ec2 management",
                            "pycharm blog", "javalobby", "apex tutorial",
                            "agile project", "scrum alliance",
                            "desktop app with javascript",
                            "build a gmail clone", "fantasy map generator",
                            "talk agile", "ng-book", "zk angular",
                            "open source rest api"],
        "keywords": ["devops", "microservice"],
        "domains": ["github.com", "stackoverflow.com", "developer.mozilla.org",
                     "docs.python.org", "npmjs.com", "docker.com", "gitlab.com",
                     "bitbucket.org", "rapidapi.com", "mockaroo.com",
                     "dreamfactory.com", "linuxize.com", "thinkful.com"],
    },
    "DataConsulting": {
        "strong_keywords": ["data consulting", "business intelligence", "power bi",
                            "powerbi", "data warehouse", "data warehousing",
                            "etl pipeline", "data engineering", "data governance",
                            "financial forecasting", "sharepoint powerbi",
                            "self-service-bi", "how up-to-date their data"],
        "keywords": ["snowflake", "bigquery", "looker"],
        "domains": ["looker.com", "getdbt.com", "snowflake.com", "ssbi-blog.de"],
    },
    "EveOnline": {
        "strong_keywords": ["eve online", "eve gate", "eve mission", "eve market",
                            "eve manufacturing", "eve pvp", "eve scout",
                            "eve skillplan", "eve-skillplan", "esi knife",
                            "spectre fleet", "new eden", "capsuleer",
                            "rifter guide", "gas site list",
                            "t3 manufacturing", "combat booster",
                            "space-mail express", "mittani", "evelopedia",
                            "eve pro guide", "npsi community",
                            "eve battlecruiser", "frigate pvp",
                            "eve mission tengu", "low sec solo",
                            "eve retribution", "evemissioneer",
                            "nolan rulgin", "eve agent browser",
                            "ccp games"],
        "keywords": [],
        "title_only": ["eve online"],
        "domains": ["eveonline.com", "eve-online.com",
                     "evemissioneer.com", "eve-skillplan.net",
                     "evemarketer.com", "esiknife.com", "eve-markets.net"],
    },
    "DiscordBOTResearch": {
        "strong_keywords": ["discord bot", "discord api", "discord server",
                            "discord.js", "discord.py", "discord webhook", "mee6",
                            "discord rule"],
        "keywords": [],
        "domains": ["discord.com", "discord.gg", "discordapp.com",
                     "discord.js.org", "mee6.xyz"],
    },
    "Drone Sites": {
        "strong_keywords": ["drone racing", "fpv racing", "quadcopter",
                            "aerial photography drone", "part 107", "faa drone"],
        "keywords": ["drone", "fpv", "quadcopter", "uav"],
        "domains": ["dji.com", "getfpv.com", "rotorbuilds.com"],
    },
    "EVETools": {
        "strong_keywords": ["zkillboard", "killboard", "eve fitting tool",
                            "eve market tool", "evepraisal", "osmium fitting",
                            "osmium loadout", "evemon", "dotlan"],
        "keywords": ["zkillboard"],
        "domains": ["zkillboard.com", "evemarketer.com", "eve-central.com",
                     "dotlan.net", "evewho.com", "evepraisal.com", "o.smium.org"],
    },
    "Geneology": {
        "strong_keywords": ["genealogy", "geneology", "family tree", "ancestry",
                            "dna testing", "family history", "birth record",
                            "death record", "findagrave", "familysearch"],
        "keywords": [],
        "domains": ["ancestry.com", "familysearch.org", "findagrave.com",
                     "23andme.com", "myheritage.com", "geni.com"],
    },
    "GW": {
        "strong_keywords": ["guild wars", "guildwars", "arenanet", "pvxwiki"],
        "keywords": [],
        "domains": ["guildwars.com", "guildwars2.com", "arenanet.com",
                     "wiki.guildwars.com", "wiki.guildwars2.com", "pvxwiki.com"],
    },
    "Healthcare": {
        "strong_keywords": ["superfood", "natural deodorant", "deodorant recipe",
                            "herb garden seed", "keto diet", "dr. berg",
                            "natural health", "vaccine adverse", "undoctored",
                            "health ranger", "underground greenhouse",
                            "year-round fresh food", "exercise science",
                            "weight loss", "taco seasoning", "naturalnews",
                            "covid treatment", "covid-19 early treatment",
                            "qigong", "wild goose qigong",
                            "dialectic behavior therapy", "dbt center",
                            "meditation masterclass", "comet impact"],
        "keywords": ["superfood", "wellness"],
        "title_only": ["health", "nutrition", "fitness", "exercise",
                       "recipe", "workout", "diet"],
        "domains": ["webmd.com", "mayoclinic.org", "healthline.com",
                     "nih.gov", "cdc.gov", "myfitnesspal.com",
                     "naturalhealth365.com", "naturalnews.com", "nuts.com",
                     "trueleafmarket.com", "drberg.com", "c19early.org",
                     "mobap.edu"],
    },
    "Hunting and Land Information": {
        "strong_keywords": ["hunting lease", "land management",
                            "wildlife conservation", "deer hunting",
                            "land for sale", "missouri department of conservation",
                            "outdoor recreation", "craftsman riding mower",
                            "craftsman lawn tractor", "sears partsdirect",
                            "trailhead salesforce"],
        "keywords": ["hunting", "wildlife"],
        "title_only": ["hunting", "fishing", "camping"],
        "domains": ["onxmaps.com", "landandfarm.com", "cabelas.com",
                     "basspro.com", "nwtf.org", "ducks.org", "rmef.org",
                     "mdc.mo.gov", "searspartsdirect.com"],
    },
    "LOL Guides": {
        "strong_keywords": ["league of legends", "lol guide", "lol build",
                            "champion.gg", "mobafire", "lol champion",
                            "lol tier list"],
        "keywords": [],
        "title_only": ["champion.gg"],
        "domains": ["op.gg", "mobafire.com", "u.gg", "champion.gg",
                     "leagueoflegends.com", "lolalytics.com", "gankster.gg"],
    },
    "NewChurch": {
        "strong_keywords": ["church online", "online ministry", "christian mentor",
                            "ministry certificate", "christian leader",
                            "king james bible", "church online platform",
                            "planning center", "ministry calling",
                            "getting started orientation"],
        "keywords": ["ministry", "sermon", "pastor"],
        "title_only": ["church", "christian", "bible"],
        "domains": ["planningcenter.com", "faithlife.com", "biblegateway.com",
                     "youversion.com", "rightnow.org", "lifeway.com",
                     "proclaimonline.com", "christianleadersinstitute.org",
                     "kingjamesbibleonline.org", "churchonlineplatform.com",
                     "christianmentors.com"],
    },
    "Personal Development": {
        "strong_keywords": ["self-improvement", "life coaching", "personal growth",
                            "playful parenting", "hand in hand parenting",
                            "emotional intelligence", "goal setting",
                            "morphic resonance", "sheldrake",
                            "passphrase generator"],
        "keywords": ["parenting"],
        "title_only": ["parenting", "self-improvement"],
        "domains": ["ted.com", "masterclass.com", "coursera.org", "udemy.com",
                     "sheldrake.org", "handinhandparenting.org"],
    },
    "PodCasts": {
        "strong_keywords": ["podcast hosting", "podcast directory",
                            "podcast editing", "descript podcast",
                            "podcast awesome", "hot sauce podcast"],
        "keywords": ["podcast", "podcasting"],
        "domains": ["anchor.fm", "podbean.com", "buzzsprout.com", "transistor.fm",
                     "podcasts.apple.com", "descript.com"],
    },
    "Politics": {
        "strong_keywords": ["conservative playbook", "liberty daily",
                            "fox news", "breitbart", "project veritas",
                            "okeefe media", "national pulse", "revolver news",
                            "newsmax", "epoch times", "daily wire",
                            "tea party coalition", "restoring liberty",
                            "federalist", "prophecy supernatural",
                            "marzulli", "mark crispin miller",
                            "news from underground", "gensix productions",
                            "america social ills", "vaccine mandate",
                            "covid jab", "whistleblower", "deplorables",
                            "great awakening", "fourth industrial revolution",
                            "geopolitical risk", "war room pandemic",
                            "made in the usa", "civil rights act",
                            "religious discrimination workplace",
                            "precinct strategy", "workplace discrimination"],
        "keywords": ["conservative"],
        "title_only": ["political", "politics"],
        "domains": ["foxnews.com", "breitbart.com", "dailywire.com",
                     "theepochtimes.com", "newsmax.com", "politico.com",
                     "thehill.com", "okeefemediagroup.com", "projectveritas.com",
                     "revolver.news", "thenationalpulse.com", "libertydaily.com",
                     "thefederalist.com", "stlouisteaparty.com",
                     "conservativeplaybook.com", "gensixproductions.com"],
    },
    "Social Media": {
        "strong_keywords": ["hashtag analytics", "hashtag ranking",
                            "twitter trend", "trending hashtag", "instagram hashtag",
                            "tiktok trending", "twitter analytics",
                            "influencer marketing", "social media management",
                            "screenshot tool", "sharex", "hashtagify",
                            "twitonomy", "trendsmap", "twubs",
                            "top hashtag", "statweestics", "whatthetrend",
                            "dubby energy", "dubby partnership",
                            "linkedin profile", "dashnex",
                            "usb pen drive linux", "boot and run linux"],
        "keywords": ["hashtag"],
        "title_only": ["twitter", "tiktok", "trending"],
        "domains": ["facebook.com", "twitter.com", "x.com", "instagram.com",
                     "tiktok.com", "linkedin.com", "pinterest.com",
                     "buffer.com", "hootsuite.com", "canva.com", "unsplash.com",
                     "later.com", "hashtagify.me", "twubs.com", "trendsmap.com",
                     "twitonomy.com", "whatthetrend.com", "top-hashtags.com",
                     "getsharex.com", "loomly.com", "dubbyenergy.com"],
    },
    "WordPressTheme": {
        "strong_keywords": ["wordpress theme", "wordpress plugin",
                            "wordpress development", "elementor", "divi theme",
                            "woocommerce", "gutenberg editor",
                            "wordpress.com"],
        "keywords": ["wordpress"],
        "domains": ["wordpress.org", "wordpress.com", "themeforest.net",
                     "elegantthemes.com", "wpengine.com", "yoast.com",
                     "ravenbluethemes.com"],
    },
    "Writing": {
        "strong_keywords": ["fiction writing", "novel writing",
                            "manuscript tool", "book title generator",
                            "character name generator", "character creator",
                            "story structure", "hero's journey",
                            "worldbuilding", "plottr", "manuskript", "autocrit",
                            "reedsy", "creative writing", "character motivation",
                            "personality generator", "fantasy book title",
                            "sci-fi book title", "adventure plot", "sudowrite",
                            "writing prompt", "science fiction movie",
                            "science fiction book", "baen books",
                            "project gutenberg", "author blog",
                            "legacy dawning chapter",
                            "world building magazine"],
        "keywords": ["manuscript", "plottr", "reedsy", "autocrit"],
        "title_only": ["writing", "author", "novel", "fiction"],
        "domains": ["reedsy.com", "grammarly.com", "scrivener.com",
                     "autocrit.com", "plottr.com", "sudowrite.com",
                     "onestopforwriters.com", "springhole.net", "rangen.co.uk",
                     "charactercreator.org", "worldbuildingmagazine.com",
                     "theologeek.ch", "shangchimokf.blogspot.com",
                     "gutenberg.org", "baen.com"],
    },
}

# Direct domain -> folder overrides for precise classification
DOMAIN_OVERRIDES = {
    # AI tools
    "sudowrite.com": "Writing", "caktus.ai": "Writing",
    "claude.ai": "Deep Learning", "openrouter.ai": "Deep Learning",
    "iki.ai": "Deep Learning", "botpress.com": "Development",
    "aiforwork.co": "BusinessTools", "daytona.io": "Development",
    "meta.ai": "Deep Learning", "notdiamond.ai": "Deep Learning",
    "aistudio.google.com": "Deep Learning",
    "colab.research.google.com": "DataScienceTools",
    "llamacoder.together.ai": "Development",
    "theresanaiforthat.com": "Deep Learning",
    "whataicandotoday.com": "Deep Learning",
    "notebooklm.google": "Deep Learning",
    "skyvern.com": "Development", "aiter.io": "BusinessTools",

    # Politics / News / Conservative media
    "zerohedge.com": "Politics", "americanthinker.com": "Politics",
    "bannonswarroom.com": "Politics", "warroom.org": "Politics",
    "brighteon.com": "Politics", "brighteon.tv": "Politics",
    "brighteon.social": "Politics", "brighteon.ai": "Politics",
    "blazetv.com": "Politics", "subscribe.blazetv.com": "Politics",
    "lifesitenews.com": "Politics", "oann.com": "Politics",
    "parler.com": "Politics", "gab.com": "Politics", "gabpay.com": "Politics",
    "weaselzippers.us": "Politics", "centipedenation.com": "Politics",
    "freespoke.com": "Politics", "censored.news": "Politics",
    "americasvoice.news": "Politics", "harbingersdaily.com": "Politics",
    "georgiastarnews.com": "Politics", "spike.news": "Politics",
    "tpn.net": "Politics", "mises.org": "Politics",
    "trevorloudon.com": "Politics", "stopworldcontrol.com": "Politics",
    "stillnessinthestorm.com": "Politics", "polymarket.com": "Politics",
    "puresocialnetwork.com": "Politics", "realscience.news": "Politics",
    "investors.com": "Politics", "preparedness.news": "Politics",
    "theethicalskeptic.com": "Politics", "savetherepublic.us": "Politics",
    "precinctstrategy.com": "Politics", "stcharlesgop.com": "Politics",
    "constitutionparty.com": "Politics", "lpmo.org": "Politics",
    "lp.org": "Politics", "redballoon.work": "Politics",
    "hawley.senate.gov": "Politics", "luetkemeyer.house.gov": "Politics",
    "senate.mo.gov": "Politics", "house.mo.gov": "Politics",
    "fpiw.org": "Politics", "dailyclout.io": "Politics",
    "childrenshealthdefense.org": "Politics",
    "americasfrontlinedoctors.org": "Politics",
    "covid19criticalcare.com": "Politics",
    "covidvaccinereactions.com": "Politics",
    "vacsafety.org": "Politics", "vaxxter.com": "Politics",
    "speakwithanmd.com": "Politics",

    # NewChurch / Religion
    "calvarychapel.com": "NewChurch", "cru.org": "NewChurch",
    "dcfi.org": "NewChurch", "sacred-texts.com": "NewChurch",
    "reformationfellowship.org": "NewChurch",
    "astudyofdenominations.com": "NewChurch",
    "housechurches.net": "NewChurch", "gty.org": "NewChurch",
    "christianleadersnetwork.org": "NewChurch",
    "christianityexplored.org": "NewChurch",
    "multiplymovement.com": "NewChurch",
    "newchurches.com": "NewChurch", "called.app": "NewChurch",
    "gracious.tech": "NewChurch", "basiltech.org": "NewChurch",
    "soulcenters.org": "NewChurch", "mattdabbs.com": "NewChurch",
    "theology-academy.org": "NewChurch", "netbible.org": "NewChurch",
    "davidfeddes.com": "NewChurch", "pseudepigrapha.com": "NewChurch",
    "miqlat.org": "NewChurch", "ttb.org": "NewChurch",
    "ifapray.org": "NewChurch", "souledout.org": "NewChurch",
    "mycatholicdoctor.com": "NewChurch",

    # EVE Online
    "eve-marketdata.com": "EVETools", "eveboard.com": "EVETools",
    "evecorptools.net": "EVETools", "eve-webtools.com": "EVETools",
    "eve-hr.com": "EVETools", "eve-hunt.net": "EVETools",
    "eveskunk.com": "EVETools", "timerboard.net": "EVETools",
    "fits.federatis.fr": "EVETools", "eve.1019.net": "EVETools",
    "eve-scout.com": "EveOnline", "spreadsheetsin.space": "EveOnline",
    "k162space.com": "EveOnline", "wormholes.info": "EveOnline",
    "dore.eve-tools.net": "EveOnline", "osmeden.com": "EveOnline",
    "evechatter.com": "EveOnline", "jita.space": "EveOnline",
    "alysii.com": "EveOnline", "rvbeve.com": "EveOnline",
    "flyreckless.com": "EveOnline", "privateershaven.enjin.com": "EveOnline",
    "pandemic-horde.org": "EveOnline",
    "auth.wintercoalition.space": "EveOnline",
    "auth.eve-linknet.com": "EveOnline",
    "updates.eve-volt.net": "EveOnline",
    "heartsandmindsalliance.org": "EveOnline",
    "littleufo.com": "EveOnline",

    # LOL Guides / Esports / Gaming
    "loldatascience.com": "LOL Guides",
    "wewillteachyouleague.com": "LOL Guides",
    "leagueofgraphs.com": "LOL Guides",
    "developer.riotgames.com": "LOL Guides",
    "dmginc.gg": "LOL Guides", "forum.dmginc.gg": "LOL Guides",
    "metatft.com": "LOL Guides", "app.mobalytics.gg": "LOL Guides",
    "tactics.tools": "LOL Guides", "tracker.gg": "LOL Guides",
    "xdx.gg": "LOL Guides", "ms.dmginc.gg": "LOL Guides",
    "start.gg": "LOL Guides", "pvp.com": "LOL Guides",
    "metafy.gg": "LOL Guides", "app.blue.cc": "LOL Guides",

    # Development / Coding
    "code.org": "Development", "codeschool.com": "Development",
    "codecademy.com": "Development", "coderbyte.com": "Development",
    "codersaurus.com": "Development", "codementor.io": "Development",
    "jsbin.com": "Development", "js-tutorial.com": "Development",
    "getbootstrap.com": "Development", "plnkr.co": "Development",
    "nodeschool.io": "Development", "codesandbox.io": "Development",
    "overapi.com": "Development", "webdevchecklist.com": "Development",
    "howtogeek.com": "Development", "thehackernews.com": "Development",
    "wolframalpha.com": "Development", "epochconverter.com": "Development",
    "gitora.com": "Development", "davidsgale.com": "Development",
    "thatjeffsmith.com": "Development", "nubuilder.net": "Development",
    "netdevops.me": "Development", "dev.smart4apex.nl": "Development",
    "dgielis.blogspot.in": "Development",
    "cline.bot": "Development", "docs.cline.bot": "Development",
    "bolt.new": "Development", "cursor.com": "Development",
    "codeium.com": "Development", "v0.dev": "Development",
    "n8n.io": "Development", "create.t3.gg": "Development",
    "vercel.com": "Development", "app.netlify.com": "Development",
    "console.neon.tech": "Development",
    "modelcontextprotocol.io": "Development",
    "pulsemcp.com": "Development", "cursor.directory": "Development",
    "docs.anthropic.com": "Development",
    "google.github.io": "Development",
    "aider.chat": "Development", "voltagent.dev": "Development",
    "app.composio.dev": "Development",
    "jsreport.net": "Development", "balsamiq.com": "Development",
    "pidoco.com": "Development", "toptal.com": "Development",
    "puppetry.app": "Development", "app.testim.io": "Development",
    "nerdydata.com": "Development", "app.codacy.com": "Development",
    "web.postman.co": "Development",
    "targetprocess.com": "Development",
    "community.jaspersoft.com": "Development",
    "docs.formtools.org": "Development",

    # BusinessTools / SaaS
    "appsumo.com": "BusinessTools", "app.clickup.com": "BusinessTools",
    "signupgenius.com": "BusinessTools", "tomsplanner.com": "BusinessTools",
    "app.budgeta.com": "BusinessTools",
    "clearcheckbook.com": "BusinessTools",
    "pipedrive.com": "BusinessTools",
    "bitwarden.com": "BusinessTools", "cloudfogger.com": "BusinessTools",
    "formswift.com": "BusinessTools", "lawdepot.com": "BusinessTools",
    "metricsparrow.com": "BusinessTools",
    "sendfox.com": "BusinessTools", "climbo.com": "BusinessTools",
    "app.climbo.com": "BusinessTools",
    "chroniclehq.com": "BusinessTools",
    "storydoc.com": "BusinessTools",
    "freeconvert.com": "BusinessTools",
    "create.vista.com": "BusinessTools",
    "easeus.com": "BusinessTools", "recorder.easeus.com": "BusinessTools",
    "streamlabs.com": "BusinessTools", "streamyard.com": "BusinessTools",
    "app.eurekaa.io": "BusinessTools", "geekpay.io": "BusinessTools",
    "greengeeks.com": "BusinessTools", "inmotionhosting.com": "BusinessTools",
    "ghost.org": "BusinessTools", "ecwid.com": "BusinessTools",
    "shopify.com": "BusinessTools",
    "kanary.com": "BusinessTools", "app.wordtune.com": "BusinessTools",
    "support.wordtune.com": "BusinessTools",
    "researchbuddy.app": "BusinessTools",
    "promptcowboy.ai": "BusinessTools",
    "promptperfect.jina.ai": "BusinessTools",
    "app.mymemo.ai": "BusinessTools", "app.frontdoor.xyz": "BusinessTools",
    "grokipedia.com": "BusinessTools",
    "clerk.com": "BusinessTools",
    "kambeo.io": "BusinessTools",
    "camp.to": "BusinessTools",
    "10015.io": "BusinessTools",

    # Business / Entrepreneurship
    "bcg.com": "Business", "greatgame.com": "Business",
    "smallbusinessrevolution.org": "Business",
    "sidehustlenation.com": "Business",
    "jamesclear.com": "Business",
    "mikemichalowicz.com": "Business",
    "liveplanner.com": "Business",
    "mauldineconomics.com": "Business",

    # Social Media
    "socialmention.com": "Social Media", "tagboard.com": "Social Media",
    "ritetag.com": "Social Media",
    "postplanner.com": "Social Media",
    "websta.me": "Social Media",
    "autreplanete.com": "Social Media",
    "mewe.com": "Social Media",
    "socialhome.network": "Social Media",
    "mastodon.social": "Social Media",
    "diasporafoundation.org": "Social Media",
    "wiki.diasporafoundation.org": "Social Media",
    "the-federation.info": "Social Media",

    # Healthcare / Wellness / Martial Arts
    "karatebyjesse.com": "Healthcare", "kyusho.com": "Healthcare",
    "ryukyu-kempo.org": "Healthcare", "zkkrkarate.com": "Healthcare",
    "usarengokai.com": "Healthcare", "gatstlouis.com": "Healthcare",
    "bodyfusionstl.com": "Healthcare", "yoqi.com": "Healthcare",
    "yugiyoga.com": "Healthcare", "mytpi.com": "Healthcare",
    "thelostherbs.com": "Healthcare",
    "onlinegardeningschool.com": "Healthcare",
    "honeyflow.com": "Healthcare",
    "selfsufficientprojects.com": "Healthcare",
    "seriouseats.com": "Healthcare",
    "pmq.com": "Healthcare",
    "nuts.com": "Healthcare",

    # Hunting and Land Information
    "landsofamerica.com": "Hunting and Land Information",
    "huntinglocator.com": "Hunting and Land Information",
    "lowrance.com": "Hunting and Land Information",
    "nadaguides.com": "Hunting and Land Information",
    "ofrpc.org": "Hunting and Land Information",
    "waynecountycollector.com": "Hunting and Land Information",

    # Geneology
    "rcky.us": "Geneology", "owsleycokyhist.org": "Geneology",
    "history.ky.gov": "Geneology", "kykinfolk.com": "Geneology",
    "jaycounty.net": "Geneology",

    # Writing / Creative
    "bookbolt.io": "Writing", "lulu.com": "Writing",
    "random-character.com": "Writing",
    "archive.org": "Writing",

    # Personal Development
    "high5test.com": "Personal Development",
    "erikthor.com": "Personal Development",
    "anyintrovert.com": "Personal Development",
    "theminimalists.com": "Personal Development",
    "minimalmaxims.com": "Personal Development",
    "brainyquote.com": "Personal Development",
    "lumosity.com": "Personal Development",
    "viacharacter.org": "Personal Development",
    "humanizingwork.com": "Personal Development",
    "attachmenttraumanetwork.com": "Personal Development",
    "attachtrauma.org": "Personal Development",

    # PodCasts
    "matchmaker.fm": "PodCasts", "toastyai.com": "PodCasts",

    # Drone Sites
    "app.airmap.com": "Drone Sites", "app.airmap.io": "Drone Sites",

    # Discord / Gaming community tools
    "shufflegazine.com": "DiscordBOTResearch",
    "discordapi.com": "DiscordBOTResearch",
    "typicalbot.com": "DiscordBOTResearch",
    "probot.io": "DiscordBOTResearch",
    "guilded.gg": "DiscordBOTResearch",

    # Sports (non-bowling, non-archery)
    "all-starperformance.net": "Healthcare",
    "armorypitching.com": "Healthcare",
    "thedynamicpitcher.com": "Healthcare",
    "practicefactorysports.com": "Healthcare",
    "rijoathletics.com": "Healthcare",
    "leaguelineup.com": "Healthcare",
    "nwseniortour.com": "Bowling",
    "greaterozarksbowling.com": "Bowling",
    "bpaa.com": "Bowling", "compusport.us": "Bowling",
    "ibpsia.com": "Bowling",

    # Education
    "abcmouse.com": "Personal Development",
    "ixl.com": "Personal Development",
    "moodle.org": "Development",
    "elearningindustry.com": "BusinessTools",

    # Crypto / Finance
    "moneymetals.com": "Banks & Credit Cards",
    "kinesis.money": "Banks & Credit Cards",
    "secureaccountview.com": "Banks & Credit Cards",
    "changenow.io": "Banks & Credit Cards",

    # Data / BI
    "data.world": "DataConsulting",
    "datavaultalliance.com": "DataConsulting",
    "mi283.us1.dbt.com": "DataConsulting",
    "catalog.data.gov": "DataConsulting",
    "enterprisedna.co": "DataConsulting",
    "portal.enterprisedna.co": "DataConsulting",
    "developer.ibm.com": "DataScienceTools",

    # Esports specific
    "battlefy.com": "LOL Guides",
    "challengermode.com": "LOL Guides",
    "context.gg": "LOL Guides",
    "cope.gg": "LOL Guides",
    "gameplan.com": "LOL Guides",
    "gamercraft.com": "LOL Guides", "play.gamercraft.com": "LOL Guides",
    "groupflows.com": "LOL Guides",
    "xpleague.com": "LOL Guides",
    "skullz.com": "LOL Guides",
    "tournamentkings.com": "LOL Guides",
    "teamliquid.com": "LOL Guides",
    "nhsbn.com": "LOL Guides",
    "usyouthbilliards.com": "LOL Guides",
    "kick.com": "Social Media",
    "twitch.tv": "Social Media",

    # Additional domain mappings for remaining items
    "wiki.eveuniversity.org": "EveOnline",
    "seat-docs.readthedocs.io": "EveOnline",
    "royalpin.com": "Bowling",
    "poolplayers.com": "Bowling",
    "trailhead.salesforce.com": "Development",
    "factorio.com": "Development",
    "eeoc.gov": "Politics",
    "upcounsel.com": "Politics",
    "medalerts.org": "Politics",
    "coronavirus.jhu.edu": "Politics",
    "nbcnews.com": "Politics",
    "agon.gg": "LOL Guides",
    "sea-thieves.com": "LOL Guides",
    "gamepress.gg": "LOL Guides",
    "gather.sh": "LOL Guides",
    "everydeveloper.com": "Development",
    "tpetrus.blogspot.com": "Development",
    "netgleb.visualstudio.com": "Development",
    "app.nocodebackend.com": "Development",
    "repoprompt.com": "Development",
    "minecraftforum.net": "Development",
    "johndcook.com": "DataScienceTools",
    "ropensci.org": "DataScienceTools",
    "traillifeusa.com": "NewChurch",
    "goodreads.com": "Writing",
    "ubersuggest.io": "BusinessTools",
    "website.com": "BusinessTools",
    "feedly.com": "BusinessTools",
    "slideshare.net": "BusinessTools",
    "lifehacker.com": "Personal Development",
    "bakadesuyo.com": "Personal Development",
    "skillet.lifehacker.com": "Healthcare",
    "workshop.lifehacker.com": "Personal Development",
    "backtoedenfilm.com": "Healthcare",
    "kfmosports.com": "Social Media",
    "reddit.com": "Social Media",
    "m.reddit.com": "Social Media",
    "medium.com": "Development",
    "mavenanalytics.io": "DataScienceTools",
    "azure.microsoft.com": "BusinessTools",
    "grow.google": "Personal Development",
    "dev.socrata.com": "DataConsulting",
    "coinmarketcap.com": "Banks & Credit Cards",
    "lode.one": "Banks & Credit Cards",
    "shop.rawconservativeopinions.com": "Politics",
    "topix.com": "Politics",
    "forbes.com": "Business",
    "drjasonfox.com": "Business",
    "grahamhancock.com": "Personal Development",
    "lutra.ai": "Development",
    "stitch.withgoogle.com": "Development",
    "biostl.org": "Business",
    "jvzoo.com": "Business",
    "docs.kluster.ai": "Development",
    "platform.kluster.ai": "Development",
}


def parse_bookmark_line(line):
    """Extract href, title from a bookmark <A> line."""
    href_match = re.search(r'HREF="([^"]*)"', line)
    title_match = re.search(r'>([^<]*)</A>', line)
    href = href_match.group(1) if href_match else ""
    title = html.unescape(title_match.group(1)) if title_match else ""
    return href, title


def word_boundary_match(keyword, text):
    """Check if keyword appears with word boundaries in text."""
    pattern = r'(?<![a-zA-Z])' + re.escape(keyword) + r'(?![a-zA-Z])'
    return bool(re.search(pattern, text, re.IGNORECASE))


def get_domain(href):
    """Extract clean domain from URL."""
    try:
        parsed = urlparse(href)
        host = (parsed.hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def score_bookmark(href, title, profile):
    """Score a bookmark against a folder profile."""
    score = 0.0
    title_lower = title.lower()
    href_lower = href.lower()
    combined = title_lower + " " + href_lower
    host = get_domain(href)

    # Domain match (strongest signal)
    for domain in profile.get("domains", []):
        d = domain.lower()
        if d == host or host.endswith("." + d):
            score += 8.0
            break

    # Strong keywords (multi-word specific phrases)
    for kw in profile.get("strong_keywords", []):
        kw_l = kw.lower()
        if kw_l in combined:
            if kw_l in title_lower:
                score += 4.0
            else:
                score += 2.0

    # Regular keywords (word-boundary matching)
    for kw in profile.get("keywords", []):
        if word_boundary_match(kw, combined):
            if word_boundary_match(kw, title_lower):
                score += 3.0
            else:
                score += 1.5

    # Title-only keywords
    for kw in profile.get("title_only", []):
        if word_boundary_match(kw, title_lower):
            score += 3.0

    return score


def parse_bookmark_file(filepath):
    """Parse Netscape bookmark HTML into header, all bookmarks, footer."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    header_lines = []
    all_bookmarks = []  # list of (line_text, current_folder, current_subfolder)
    folder_meta = OrderedDict()  # folder_name -> {"attrs": ..., "subfolders": {name: attrs}}

    i = 0
    while i < len(lines):
        header_lines.append(lines[i])
        if 'PERSONAL_TOOLBAR_FOLDER="true"' in lines[i]:
            break
        i += 1
    i += 1
    header_lines.append(lines[i])  # <DL><p>
    i += 1

    current_folder = None
    current_subfolder = None
    folder_depth = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if folder_depth == 0 and stripped == '</DL><p>' and current_folder is None:
            break

        if '<H3' in stripped and '</H3>' in stripped:
            name_match = re.search(r'>([^<]+)</H3>', stripped)
            folder_name = html.unescape(name_match.group(1)) if name_match else "Unknown"
            attrs_match = re.search(r'<H3([^>]*)>', stripped)
            folder_attrs = attrs_match.group(1) if attrs_match else ""

            if folder_depth == 0:
                current_folder = folder_name
                current_subfolder = None
                if folder_name not in ("Uncategorized", "Other"):
                    folder_meta[folder_name] = {"attrs": folder_attrs, "subfolders": OrderedDict()}
                i += 1  # skip <DL><p>
                folder_depth = 1
            elif folder_depth == 1 and current_folder:
                current_subfolder = folder_name
                if current_folder in folder_meta and folder_name not in ("Uncategorized", "Other"):
                    folder_meta[current_folder]["subfolders"][folder_name] = folder_attrs
                i += 1
                folder_depth = 2
            i += 1
            continue

        if stripped == '</DL><p>':
            if folder_depth == 2:
                current_subfolder = None
                folder_depth = 1
            elif folder_depth == 1:
                current_folder = None
                folder_depth = 0
            i += 1
            continue

        if '<A HREF=' in stripped:
            all_bookmarks.append((line, current_folder, current_subfolder))
            i += 1
            continue

        i += 1

    footer_lines = []
    while i < len(lines):
        footer_lines.append(lines[i])
        i += 1

    return header_lines, folder_meta, all_bookmarks, footer_lines


def classify_bookmark(href, title, folder_profiles, domain_overrides):
    """Classify a bookmark into the best folder."""
    if not href:
        return "Other", 0

    host = get_domain(href)

    # Check domain overrides first (most reliable)
    for domain, folder in domain_overrides.items():
        if domain == host or host.endswith("." + domain):
            if folder == "Other":
                return "Other", 0
            return folder, 10.0

    best_folder = "Other"
    best_score = 0.0
    all_scores = {}

    for folder_name, profile in folder_profiles.items():
        s = score_bookmark(href, title, profile)
        all_scores[folder_name] = s
        if s > best_score:
            best_score = s
            best_folder = folder_name

    if best_score < MIN_SCORE_THRESHOLD:
        return "Other", best_score

    # Specificity: prefer more specific folder when scores are close
    SPECIFIC_OVER_GENERAL = {
        "Deep Learning": ["Development", "Business", "BusinessTools"],
        "DataScienceTools": ["Development", "Business"],
        "DataConsulting": ["Development", "Business", "BusinessTools"],
        "EveOnline": ["Development", "Social Media"],
        "EVETools": ["Development", "EveOnline"],
        "Bowling": ["Healthcare", "Business"],
        "Archery": ["Hunting and Land Information"],
        "LOL Guides": ["Development"],
        "GW": ["Development"],
        "Writing": ["Personal Development", "Business", "Deep Learning"],
        "NewChurch": ["Personal Development", "Politics"],
        "PodCasts": ["Business", "BusinessTools"],
        "DiscordBOTResearch": ["Development"],
        "WordPressTheme": ["Development", "BusinessTools"],
    }

    for specific, generals in SPECIFIC_OVER_GENERAL.items():
        if best_folder in generals:
            specific_score = all_scores.get(specific, 0)
            if specific_score >= MIN_SCORE_THRESHOLD and specific_score >= best_score * 0.6:
                best_folder = specific
                best_score = specific_score

    return best_folder, best_score


def render_bookmarks_html(header_lines, folder_meta, folder_bookmarks, other_bookmarks, footer_lines):
    """Render the complete bookmark HTML."""
    output = []
    output.extend(header_lines)

    folder_indent = "        "
    bookmark_indent = "            "
    subfolder_indent = "            "
    sub_bookmark_indent = "                "

    def sort_key(line):
        _, t = parse_bookmark_line(line)
        return t.lower()

    SUBFOLDER_PARENTS = {"DataConsulting": "Development", "EveOnline": "Development"}

    for folder_name, meta in folder_meta.items():
        attrs = meta["attrs"]
        escaped_name = html.escape(folder_name)
        output.append(f'{folder_indent}<DT><H3{attrs}>{escaped_name}</H3>')
        output.append(f'{folder_indent}<DL><p>')

        # Subfolders
        for sub_name, sub_attrs in meta.get("subfolders", {}).items():
            escaped_sub_name = html.escape(sub_name)
            output.append(f'{subfolder_indent}<DT><H3{sub_attrs}>{escaped_sub_name}</H3>')
            output.append(f'{subfolder_indent}<DL><p>')
            sub_bms = folder_bookmarks.get(f"{folder_name}/{sub_name}", [])
            for bm in sorted(sub_bms, key=sort_key):
                output.append(f'{sub_bookmark_indent}{bm.strip()}')
            output.append(f'{subfolder_indent}</DL><p>')

        # Folder bookmarks (excluding subfolder bookmarks)
        folder_bms = folder_bookmarks.get(folder_name, [])
        for bm in sorted(folder_bms, key=sort_key):
            output.append(f'{bookmark_indent}{bm.strip()}')

        output.append(f'{folder_indent}</DL><p>')

    if other_bookmarks:
        output.append(f'{folder_indent}<DT><H3>Other</H3>')
        output.append(f'{folder_indent}<DL><p>')
        for bm in sorted(other_bookmarks, key=sort_key):
            output.append(f'{bookmark_indent}{bm.strip()}')
        output.append(f'{folder_indent}</DL><p>')

    output.extend(footer_lines)
    return '\n'.join(output)


def validate(filepath):
    """Validate the output."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    urls = re.findall(r'HREF="([^"]*)"', content)
    unique_urls = set(urls)
    dl_open = content.count('<DL><p>')
    dl_close = content.count('</DL><p>')

    folder_names = re.findall(r'<H3[^>]*>([^<]+)</H3>', content)
    folder_names_clean = [html.unescape(f) for f in folder_names if f not in ("Bookmarks",)]
    dup_folders = [f for f in set(folder_names_clean) if folder_names_clean.count(f) > 1]

    print(f"\n=== Validation Results ===")
    print(f"Total URLs found: {len(urls)}")
    print(f"Unique URLs: {len(unique_urls)}")
    if len(urls) != len(unique_urls):
        print(f"  WARNING: {len(urls) - len(unique_urls)} duplicate URLs")
    else:
        print(f"  OK: All URLs unique")
    print(f"DL open tags: {dl_open}, close tags: {dl_close}")
    if dl_open != dl_close:
        print(f"  WARNING: Mismatched DL tags!")
    else:
        print(f"  OK: DL tags balanced")
    if dup_folders:
        print(f"  WARNING: Duplicate folder names: {dup_folders}")
    else:
        print(f"  OK: No duplicate folder names")
    empty_pattern = re.findall(r'<DL><p>\s*</DL><p>', content)
    if empty_pattern:
        print(f"  WARNING: {len(empty_pattern)} empty folders")
    else:
        print(f"  OK: No empty folders")

    return len(urls), len(unique_urls), dl_open == dl_close


def main():
    print("Parsing bookmark file...")
    header_lines, folder_meta, all_bookmarks, footer_lines = parse_bookmark_file(INPUT_FILE)

    print(f"Found {len(folder_meta)} named folders")
    print(f"Found {len(all_bookmarks)} total bookmarks")

    # Classify every bookmark
    SUBFOLDER_MAP = {"DataConsulting": "Development", "EveOnline": "Development"}

    folder_bookmarks = defaultdict(list)  # folder_name or "folder/subfolder" -> [lines]
    other_bookmarks = []
    moves = defaultdict(lambda: defaultdict(list))  # from_folder -> to_folder -> [titles]

    for line, orig_folder, orig_subfolder in all_bookmarks:
        href, title = parse_bookmark_line(line)
        folder, score = classify_bookmark(href, title, FOLDER_PROFILES, DOMAIN_OVERRIDES)

        # Determine where it ends up
        if folder == "Other":
            other_bookmarks.append(line)
            if orig_folder and orig_folder not in ("Uncategorized", "Other"):
                orig_key = f"{orig_folder}/{orig_subfolder}" if orig_subfolder else orig_folder
                moves[orig_key]["Other"].append(title[:60])
        elif folder in SUBFOLDER_MAP:
            parent = SUBFOLDER_MAP[folder]
            key = f"{parent}/{folder}"
            folder_bookmarks[key].append(line)
            orig_key = f"{orig_folder}/{orig_subfolder}" if orig_subfolder else (orig_folder or "loose")
            if orig_key != key:
                moves[orig_key][key].append(title[:60])
        else:
            folder_bookmarks[folder].append(line)
            orig_key = f"{orig_folder}/{orig_subfolder}" if orig_subfolder else (orig_folder or "loose")
            if orig_key != folder:
                moves[orig_key][folder].append(title[:60])

    # Count
    total_in_folders = sum(len(v) for v in folder_bookmarks.values())
    total_other = len(other_bookmarks)
    total = total_in_folders + total_other

    print(f"\n=== Classification Results ===")
    print(f"In named folders: {total_in_folders}")
    print(f"In 'Other': {total_other}")
    print(f"Total: {total}")

    print(f"\n=== Final folder counts ===")
    for fname in folder_meta:
        count = len(folder_bookmarks.get(fname, []))
        for sub_name in folder_meta[fname].get("subfolders", {}):
            key = f"{fname}/{sub_name}"
            count += len(folder_bookmarks.get(key, []))
        print(f"  {fname}: {count}")
    print(f"  Other: {total_other}")
    print(f"  TOTAL: {total}")

    # Show significant moves (bookmarks that changed folders)
    print(f"\n=== Bookmark movements ===")
    for from_folder, tos in sorted(moves.items()):
        for to_folder, titles in sorted(tos.items()):
            if from_folder != to_folder:
                print(f"\n  {from_folder} -> {to_folder} ({len(titles)} bookmarks):")
                for t in sorted(titles)[:10]:
                    print(f"    - {t}")
                if len(titles) > 10:
                    print(f"    ... and {len(titles) - 10} more")

    # Render
    print(f"\nRendering output file...")
    html_output = render_bookmarks_html(header_lines, folder_meta, folder_bookmarks, other_bookmarks, footer_lines)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_output)

    print(f"Written to {OUTPUT_FILE}")
    validate(OUTPUT_FILE)


if __name__ == "__main__":
    main()
