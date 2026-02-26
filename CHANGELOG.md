# Changelog

## [1.4.0](https://github.com/Alberto-Codes/docvet/compare/v1.3.0...v1.4.0) (2026-02-26)


### Features

* **ci:** add post-publish PyPI smoke test ([#134](https://github.com/Alberto-Codes/docvet/issues/134)) ([5b89f3d](https://github.com/Alberto-Codes/docvet/commit/5b89f3dfd5ba520e9d5c47a3a71d382471e0a33a))
* **cli:** add per-check timing and total execution time ([#140](https://github.com/Alberto-Codes/docvet/issues/140)) ([56c6c62](https://github.com/Alberto-Codes/docvet/commit/56c6c62712c3ef333725fa742c1df3787ca7fde1)), closes [#24](https://github.com/Alberto-Codes/docvet/issues/24)
* **cli:** add progress bar for file processing ([#139](https://github.com/Alberto-Codes/docvet/issues/139)) ([0f5e5dd](https://github.com/Alberto-Codes/docvet/commit/0f5e5dd596c5940c97f21fd37e3c2e45a2d7da75)), closes [#24](https://github.com/Alberto-Codes/docvet/issues/24)
* **discovery:** add trailing-slash and double-star pattern support ([3696e6a](https://github.com/Alberto-Codes/docvet/commit/3696e6a2f36c516578db43de1a07646280ee3a5a))
* **discovery:** add trailing-slash and double-star pattern support ([#137](https://github.com/Alberto-Codes/docvet/issues/137)) ([3696e6a](https://github.com/Alberto-Codes/docvet/commit/3696e6a2f36c516578db43de1a07646280ee3a5a))
* **docs:** add breadcrumb back-links to rule pages ([#136](https://github.com/Alberto-Codes/docvet/issues/136)) ([17e985b](https://github.com/Alberto-Codes/docvet/commit/17e985bf0581071c680bc617451ca35b842a41e1))


### Bug Fixes

* **docs:** remove redundant f-string in rule_header macro ([17e985b](https://github.com/Alberto-Codes/docvet/commit/17e985bf0581071c680bc617451ca35b842a41e1))


### Documentation

* **cli:** add story 20.2 implementation record ([56c6c62](https://github.com/Alberto-Codes/docvet/commit/56c6c62712c3ef333725fa742c1df3787ca7fde1))

## [1.3.0](https://github.com/Alberto-Codes/docvet/compare/v1.2.1...v1.3.0) (2026-02-25)


### Features

* **config:** add extend-exclude configuration key ([#131](https://github.com/Alberto-Codes/docvet/issues/131)) ([15aa4ff](https://github.com/Alberto-Codes/docvet/commit/15aa4ffd99ea7b4efeb0ab2c98f657b40952cbdf)), closes [#18](https://github.com/Alberto-Codes/docvet/issues/18)


### Documentation

* **config:** add extend-exclude to configuration reference ([6711525](https://github.com/Alberto-Codes/docvet/commit/67115259c47e57ffdf8815df21a0fcac8644b5ee))

## [1.2.1](https://github.com/Alberto-Codes/docvet/compare/v1.2.0...v1.2.1) (2026-02-25)


### Bug Fixes

* **ci:** add retry logic to TestPyPI publish workflow ([08bff6f](https://github.com/Alberto-Codes/docvet/commit/08bff6f731449a6ad1454f17e25f43a615e0a8d9))
* **ci:** drop check-url that conflicts with --index in uv publish ([799237b](https://github.com/Alberto-Codes/docvet/commit/799237b9aad0d9277ad4fc0709ab86764c0110c3))
* **ci:** make test-publish resilient to TestPyPI 503s ([cc51369](https://github.com/Alberto-Codes/docvet/commit/cc513697e74789b7cd1895f4d1f2fa23edcd8280))
* **ci:** use env var for check-url to avoid flag conflict ([3b6d114](https://github.com/Alberto-Codes/docvet/commit/3b6d11428a683a982f1eca18bc2b8357e3562094))


### Documentation

* add social preview and update tagline ([#129](https://github.com/Alberto-Codes/docvet/issues/129)) ([b88f441](https://github.com/Alberto-Codes/docvet/commit/b88f4413c816dd750b2389f6052180c2de50a325))
* fix stale branch refs and version numbers across documentation ([#118](https://github.com/Alberto-Codes/docvet/issues/118)) ([36912ff](https://github.com/Alberto-Codes/docvet/commit/36912ff9fe1c7bae137aed4147a3e788315023cc))
* **site:** bump version examples to v1.2.0 in CI integration page ([36912ff](https://github.com/Alberto-Codes/docvet/commit/36912ff9fe1c7bae137aed4147a3e788315023cc))
* **site:** update CI badge to target main branch ([36912ff](https://github.com/Alberto-Codes/docvet/commit/36912ff9fe1c7bae137aed4147a3e788315023cc))
* update development guide for single-branch workflow ([36912ff](https://github.com/Alberto-Codes/docvet/commit/36912ff9fe1c7bae137aed4147a3e788315023cc))

## [1.2.0](https://github.com/Alberto-Codes/docvet/compare/v1.1.2...v1.2.0) (2026-02-25)


### Features

* **enrichment:** tighten cross-reference rule to require linkable syntax ([9520248](https://github.com/Alberto-Codes/docvet/commit/9520248b23a40bacc55c9dc4b2905674c304d50a))


### Documentation

* add develop-main sync strategy to CLAUDE.md ([ca0ad3f](https://github.com/Alberto-Codes/docvet/commit/ca0ad3fe7ac9f9b50a561c059d5b476411f200cc))
* **config:** mkdocstrings configuration overhaul ([bb736eb](https://github.com/Alberto-Codes/docvet/commit/bb736ebafabce3ce578b2c0a60b903b53f2ea0b0))
* **enrichment:** convert See Also entries to clickable cross-reference links ([f2ba236](https://github.com/Alberto-Codes/docvet/commit/f2ba236c108a319a93a6b5b94b584f1503aebc35))
* **enrichment:** update cross-reference rule page for bracket syntax ([9520248](https://github.com/Alberto-Codes/docvet/commit/9520248b23a40bacc55c9dc4b2905674c304d50a))

## [1.1.2](https://github.com/Alberto-Codes/docvet/compare/v1.1.1...v1.1.2) (2026-02-25)


### Bug Fixes

* **ci:** rename action to Docvet Check for marketplace publishing ([6ea3fbb](https://github.com/Alberto-Codes/docvet/commit/6ea3fbbd50aa3f77bafd73a478d5e4c37fec37cf))

## [1.1.1](https://github.com/Alberto-Codes/docvet/compare/v1.1.0...v1.1.1) (2026-02-24)


### Bug Fixes

* **ci:** clean up duplicate changelog entries and phantom v1.0.1 section ([99ca054](https://github.com/Alberto-Codes/docvet/commit/99ca0545987f746f93a12359da1f858faf197a41))
* **ci:** resolve release-please changelog duplication ([#93](https://github.com/Alberto-Codes/docvet/issues/93)) ([99ca054](https://github.com/Alberto-Codes/docvet/commit/99ca0545987f746f93a12359da1f858faf197a41))
* **ci:** update release-please manifest version from 1.0.2 to 1.1.0 ([99ca054](https://github.com/Alberto-Codes/docvet/commit/99ca0545987f746f93a12359da1f858faf197a41))


### Documentation

* add CI Integration page with GitHub Action and pre-commit snippets ([#96](https://github.com/Alberto-Codes/docvet/issues/96)) ([af9b92d](https://github.com/Alberto-Codes/docvet/commit/af9b92d9bde8def8b88aab8d73490e71406ab9ee))
* add navigation links row to README for marketplace visitors ([1889d8a](https://github.com/Alberto-Codes/docvet/commit/1889d8afc38fff76c1d2290c269da5c1b15c5472))
* update docvet badge to purple branding ([4e29e04](https://github.com/Alberto-Codes/docvet/commit/4e29e0422148bf19d562377f01ed7111d5a8d65e))

## [1.0.2](https://github.com/Alberto-Codes/docvet/compare/v1.0.0...v1.0.2) (2026-02-23)


### Bug Fixes

* add missing Change Log subsection to story template ([#77](https://github.com/Alberto-Codes/docvet/issues/77)) ([46055de](https://github.com/Alberto-Codes/docvet/commit/46055decb438b6e587d7d7780643b37eeb98d87b))
* **api-ref:** add error handling to _has_empty_all in gen_ref_pages ([1704fce](https://github.com/Alberto-Codes/docvet/commit/1704fce4b37aa050b97487794127edf73f57286b))
* **ci:** add contents read permission to test-publish workflow ([601b035](https://github.com/Alberto-Codes/docvet/commit/601b035f0d6a2c51f154a5635021f32dbd646fbd))
* **ci:** add target-branch main to release-please action ([538d06b](https://github.com/Alberto-Codes/docvet/commit/538d06bcdeb16061f4f1f7ca7cfebccdb354b0e0))
* **ci:** add target-branch to release-please config ([#85](https://github.com/Alberto-Codes/docvet/issues/85)) ([3d8c02e](https://github.com/Alberto-Codes/docvet/commit/3d8c02ebf53b381f8ca5be7b512b8efbe9fb0f79))
* **ci:** add TestPyPI index config for uv publish --index testpypi ([8da04cc](https://github.com/Alberto-Codes/docvet/commit/8da04cc25a6d805567860efa115258b7b15fef63))
* **ci:** use --index testpypi for correct OIDC token exchange ([e344731](https://github.com/Alberto-Codes/docvet/commit/e3447316cf69f4d4dfbde0b71b120ae4c36f9574))
* **ci:** use correct attest-action version (v0.0.4, not v1) ([2cf75fd](https://github.com/Alberto-Codes/docvet/commit/2cf75fdbb63b13de8e35bdba4bcb8113ffccda22))
* remove sonar.branch.name property incompatible with Community Edition ([50aaf65](https://github.com/Alberto-Codes/docvet/commit/50aaf655cb28bb12d1e623aa7eaff126e5509a8d))


### Documentation

* **api-ref:** auto-generated API reference pages ([#81](https://github.com/Alberto-Codes/docvet/issues/81)) ([1704fce](https://github.com/Alberto-Codes/docvet/commit/1704fce4b37aa050b97487794127edf73f57286b))
* **cli:** add 19 rule reference pages with YAML catalog and macros scaffold ([#71](https://github.com/Alberto-Codes/docvet/issues/71)) ([6ab45f6](https://github.com/Alberto-Codes/docvet/commit/6ab45f6bb363349ddd7d82d8fd4ba8d7e3234979))
* **cli:** add check pages, configuration reference, and site design ([#68](https://github.com/Alberto-Codes/docvet/issues/68)) ([2408d1c](https://github.com/Alberto-Codes/docvet/commit/2408d1ca06948f83970489adcae6491d5f445d53))
* **cli:** scaffold documentation site with Getting Started and CLI Reference ([#67](https://github.com/Alberto-Codes/docvet/issues/67)) ([42d43d6](https://github.com/Alberto-Codes/docvet/commit/42d43d61ae9b195ebe6d601cb1febb0e4b50dbaf))
* **config:** add Configuration Reference page ([2408d1c](https://github.com/Alberto-Codes/docvet/commit/2408d1ca06948f83970489adcae6491d5f445d53))
* **coverage:** add Coverage Check documentation page ([2408d1c](https://github.com/Alberto-Codes/docvet/commit/2408d1ca06948f83970489adcae6491d5f445d53))
* **enrichment:** add Enrichment Check documentation page ([2408d1c](https://github.com/Alberto-Codes/docvet/commit/2408d1ca06948f83970489adcae6491d5f445d53))
* **freshness:** add Freshness Check documentation page ([2408d1c](https://github.com/Alberto-Codes/docvet/commit/2408d1ca06948f83970489adcae6491d5f445d53))
* **glossary:** add abbreviations file with 22 domain term tooltips ([6c64670](https://github.com/Alberto-Codes/docvet/commit/6c646700110dd80e2749cb2ff2be777a71110515))
* **glossary:** add browsable glossary reference page ([6c64670](https://github.com/Alberto-Codes/docvet/commit/6c646700110dd80e2749cb2ff2be777a71110515))
* **glossary:** add capitalized variants for complete tooltip coverage ([6c64670](https://github.com/Alberto-Codes/docvet/commit/6c646700110dd80e2749cb2ff2be777a71110515))
* **glossary:** add domain glossary with inline tooltips ([#79](https://github.com/Alberto-Codes/docvet/issues/79)) ([6c64670](https://github.com/Alberto-Codes/docvet/commit/6c646700110dd80e2749cb2ff2be777a71110515))
* **griffe:** add Griffe Check documentation page ([2408d1c](https://github.com/Alberto-Codes/docvet/commit/2408d1ca06948f83970489adcae6491d5f445d53))

## [1.0.0](https://github.com/Alberto-Codes/docvet/releases/tag/v1.0.0) (2026-02-21)

### Features

* **enrichment:** 10 rules detecting missing docstring sections — Raises, Yields, Receives, Warns, Other Parameters, Attributes, Typed Attributes, Examples, Cross-references, and fenced code blocks
* **freshness:** 5 rules detecting stale docstrings — signature changes (HIGH), body changes (MEDIUM), import changes (LOW), git-blame drift, and age-based staleness
* **coverage:** missing `__init__.py` detection for mkdocs discoverability
* **griffe:** 3 rules capturing griffe parser warnings for mkdocs rendering compatibility
* **reporting:** markdown and terminal output with configurable formats
* **cli:** 5 subcommands (check, enrichment, freshness, coverage, griffe) with `--staged`, `--all`, `--files`, `--format`, and `--output` options
* **integrations:** pre-commit hook and GitHub Action for CI/CD pipelines
* **config:** `[tool.docvet]` section in pyproject.toml with per-check configuration
