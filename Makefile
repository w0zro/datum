# datum -- build, verify, release.
#
#   make check     verify everything CI verifies, locally
#   make build     regenerate every port + the previews
#   make release   tag the next patch version and push (CI publishes)
#   make release VERSION=0.2.0    tag an explicit version
#
# Releases are driven entirely by the tag: release.yml packages the extension
# as ${TAG#v}, so the tag IS the published version -- nothing to bump by hand.

.PHONY: default check build previews release

default: check

# Everything .github/workflows/check.yml runs, minus the Neovim load test
# (which needs nvim on PATH; run `make check-nvim` for that).
check:
	@python3 tools/derive.py --check
	@python3 tools/gen_ports.py --check
	@python3 tools/gen_preview.py --check
	@echo "all checks passed"

check-nvim:
	@nvim --headless -u NONE -c "set rtp+=$(CURDIR)" \
	  -c "set background=dark"  -c "colorscheme datum" \
	  -c "set background=light" -c "colorscheme datum" -c "qa" 2>/tmp/datum_nvim_err
	@test ! -s /tmp/datum_nvim_err || (cat /tmp/datum_nvim_err; exit 1)
	@echo "colorscheme loads clean in both modes"

build:
	@python3 tools/gen_ports.py
	@python3 tools/gen_preview.py

previews:
	@python3 tools/gen_preview.py

# Next patch after the highest existing v-tag, unless VERSION= is given.
VERSION ?= $(shell git tag -l 'v*' | sed 's/^v//' | sort -V | tail -1 | \
             awk -F. '{printf "%d.%d.%d", $$1, $$2, $$3+1}')
TAG = v$(VERSION)

release:
	@test -z "$$(git status --porcelain)" || { echo "working tree is dirty"; exit 1; }
	@test "$$(git rev-parse --abbrev-ref HEAD)" = "main" || { echo "not on main"; exit 1; }
	@git rev-parse -q --verify "refs/tags/$(TAG)" >/dev/null && \
	  { echo "$(TAG) already exists"; exit 1; } || true
	@$(MAKE) --no-print-directory check
	@git fetch -q origin && test -z "$$(git log origin/main..HEAD --oneline)" || \
	  { echo "unpushed commits -- run: git push origin main"; exit 1; }
	@git tag -a "$(TAG)" -m "datum $(TAG)"
	@git push origin "$(TAG)"
	@echo "pushed $(TAG) -- release.yml is publishing to the Marketplace + Open VSX"
