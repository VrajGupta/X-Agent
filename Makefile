.PHONY: graph-index graph-index-check graph-links-check

graph-index:
	node scripts/build-graph-index.mjs

graph-index-check:
	node scripts/build-graph-index.mjs --check

graph-links-check:
	node scripts/build-graph-index.mjs --check-links
