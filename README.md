# vraj ai digest

A tiny no-dependency local content studio that turns AI sources into copy-ready field notes for Vraj.

A tiny no-dependency job that:

1. reads AlphaSignal's RSS feed
2. reads recent AI posts from X when `X_BEARER_TOKEN` is set
3. rewrites each item in plain technical language when `OPENAI_API_KEY` is set
4. writes an RSS file at `out/ai-digest.xml`
5. writes a copy-and-paste page at `out/index.html`
6. personalizes original posts, opinions, replies, repost comments and image ideas from `profile.json`
7. can post one reviewed item to X with an explicit `--post`

It uses the official X API rather than scraping X.

## run it

```sh
cp .env.example .env
# fill in the keys you actually have
python3 ai_digest.py
```

The feed works without either key using AlphaSignal's public feed and deterministic personalized fallback packs. The LLM key improves the wording and variety but is optional. Edit `profile.json` to change Vraj's projects, voice, themes, opinions and things to avoid. X search can use a bearer token or the user token created below.

## connect X once

Create an X developer app and configure this exact callback URL:

```text
http://127.0.0.1:8765/callback
```

Put the app client ID in `.env`, then run this locally:

```sh
python3 x_auth.py
```

It opens X in your browser, waits for your approval, and writes the access and refresh tokens to `.env` with file mode `600`. It never prints the token. The requested scopes are `tweet.read users.read tweet.write offline.access`.

Post one clearly labeled test message:

```sh
python3 ai_digest.py --test-post
```

Review `out/ai-digest.xml`, then post at most one new digest item:

```sh
python3 ai_digest.py --post
```

Posting is off by default. The script never asks for credentials in chat and never posts a batch.

## schedule it

Run hourly with cron:

```cron
0 * * * * cd /absolute/path/to/miscellaneous && /usr/bin/python3 ai_digest.py >> out/job.log 2>&1
```

The dashboard is copy-first by design: it does not silently post, scrape X, or invent source stats. Open the copy-and-paste page directly or serve it locally:

```sh
open out/index.html
python3 -m http.server 8080 --directory out
```

## tune the X topics

Edit `x_queries` in `config.json`. Keep the query focused; one good query is better than scraping the whole platform. For example:

```json
"x_queries": [
  "(agents OR \"code agents\" OR MCP) -is:retweet lang:en",
  "(LLM OR reasoning OR evals OR RLHF) -is:retweet lang:en",
  "(inference OR GPUs OR RAG OR \"prompt injection\") -is:retweet lang:en"
]
```

## checks

```sh
python3 -m unittest -v
python3 ai_digest.py --self-test
```
