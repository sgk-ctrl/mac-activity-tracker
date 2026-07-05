"""Category + display-name mappings. Edit these to match your own apps and
what you personally consider focus vs. distraction. Kept as plain data so
non-Python contributors can PR changes safely."""

# bundle id -> (display name, category)
APP_CATEGORY = {
    "com.apple.dt.Xcode":            ("Xcode", "Coding"),
    "com.microsoft.VSCode":          ("VS Code", "Coding"),
    "com.todesktop.230313mzl4w4u92": ("Cursor", "Coding"),
    "com.googlecode.iterm2":         ("iTerm2", "Coding"),
    "com.apple.Terminal":            ("Terminal", "Coding"),
    "dev.warp.Warp-Stable":          ("Warp", "Coding"),
    "com.jetbrains.pycharm":         ("PyCharm", "Coding"),
    "com.sublimetext.4":             ("Sublime Text", "Coding"),
    "com.google.Chrome":             ("Google Chrome", "Browsing"),
    "com.apple.Safari":              ("Safari", "Browsing"),
    "company.thebrowser.Browser":    ("Arc", "Browsing"),
    "org.mozilla.firefox":           ("Firefox", "Browsing"),
    "com.tinyspeck.slackmacgap":     ("Slack", "Communication"),
    "com.apple.mail":                ("Mail", "Communication"),
    "com.apple.iChat":               ("Messages", "Communication"),
    "com.hnc.Discord":               ("Discord", "Communication"),
    "us.zoom.xos":                   ("Zoom", "Meetings"),
    "notion.id":                     ("Notion", "Docs / Notes"),
    "md.obsidian":                   ("Obsidian", "Docs / Notes"),
    "com.apple.Notes":               ("Notes", "Docs / Notes"),
    "com.apple.Preview":             ("Preview", "Docs / Notes"),
    "com.figma.Desktop":             ("Figma", "Design"),
    "com.spotify.client":            ("Spotify", "Media"),
    "com.apple.Music":               ("Music", "Media"),
    "com.anthropic.claude":          ("Claude", "AI / Agentic"),
}

# app bundle-id fragments that indicate an agentic / AI tool
AGENTIC_APP_FRAGMENTS = ["claude", "cursor", "codex", "hermes", "copilot"]

# ordered (regex, category) — first match wins
DOMAIN_CATEGORY = [
    (r"(github|gitlab|stackoverflow|python\.org|developer\.|npmjs|vercel|localhost)", "Coding"),
    (r"(claude\.ai|chatgpt|openai|perplexity|gemini|huggingface)", "AI / Agentic"),
    (r"(youtube|netflix|twitch|spotify)", "Media"),
    (r"(twitter|x\.com|reddit|linkedin|instagram|facebook|tiktok)", "Social"),
    (r"(mail\.google|gmail|outlook)", "Communication"),
    (r"(calendar\.google|calendly|zoom\.us)", "Meetings"),
    (r"(notion|docs\.google|confluence)", "Docs / Notes"),
    (r"(figma|dribbble|behance)", "Design"),
    (r"(amazon|ebay|etsy)", "Shopping"),
    (r"(news|nytimes|medium|substack|arxiv)", "News / Reading"),
]

AGENTIC_DOMAINS = r"(claude\.ai|chatgpt|openai|codex|hermes)"

# exact argv[0] basenames considered agentic CLI tools
AGENTIC_CLI = {"claude", "codex", "hermes", "aider", "cursor", "llm", "ollama"}

# categories that count as focused deep work vs. distraction (used by the dashboard too)
FOCUS_CATEGORIES = {"Coding", "AI / Agentic"}
DISTRACTION_CATEGORIES = {"Social", "Media", "Shopping"}
