# Changelog

## [1.13.0](https://github.com/Alberto-Codes/docvet/compare/v1.12.1...v1.13.0) (2026-03-08)


### Features

* **enrichment:** add missing-returns rule for undocumented return values ([#334](https://github.com/Alberto-Codes/docvet/issues/334)) ([31faf3d](https://github.com/Alberto-Codes/docvet/commit/31faf3d189159d44344f1935d41886acf699e2f6))
* **enrichment:** add NumPy-style section recognition ([#344](https://github.com/Alberto-Codes/docvet/issues/344)) ([62ce6ed](https://github.com/Alberto-Codes/docvet/commit/62ce6edc598a2265fe4cf5aa7e0f6ecfd0f80d7c))
* **enrichment:** add Sphinx/RST docstring style support ([#332](https://github.com/Alberto-Codes/docvet/issues/332)) ([1bbd18f](https://github.com/Alberto-Codes/docvet/commit/1bbd18fc788474d27223d9bbb07bdf853e2ebd0a))
* **presence:** add overload-has-docstring rule ([0d83358](https://github.com/Alberto-Codes/docvet/commit/0d8335807ed8968c97bd6242f8a990f6753e3c85))


### Bug Fixes

* **enrichment:** address code review findings for Story 34.1 ([1bbd18f](https://github.com/Alberto-Codes/docvet/commit/1bbd18fc788474d27223d9bbb07bdf853e2ebd0a))

## [1.12.1](https://github.com/Alberto-Codes/docvet/compare/v1.12.0...v1.12.1) (2026-03-07)


### Bug Fixes

* **cli:** catch ImportError in mcp command for missing extras ([062072d](https://github.com/Alberto-Codes/docvet/commit/062072de88dd8f40543bfa66c10245f957d2403a))
* **docs:** wrap GitHub Actions code blocks with raw tags ([3f1763d](https://github.com/Alberto-Codes/docvet/commit/3f1763d8de3413ee2610da2dd122b24bfe0a0a44))

## [1.12.0](https://github.com/Alberto-Codes/docvet/compare/v1.11.0...v1.12.0) (2026-03-07)


### Features

* **ci:** add badge outputs to GitHub Action and dynamic badge docs ([#313](https://github.com/Alberto-Codes/docvet/issues/313)) ([4e4a09a](https://github.com/Alberto-Codes/docvet/commit/4e4a09a1b8af3e3d81aecff5f81a54b3218f3b67))
* **cli:** add --summary flag for per-check quality percentages ([#314](https://github.com/Alberto-Codes/docvet/issues/314)) ([3a225d3](https://github.com/Alberto-Codes/docvet/commit/3a225d31102f70f163a062b7c421bd05153dd926))
* **cli:** add `docvet config` command and remove interrogate ([#316](https://github.com/Alberto-Codes/docvet/issues/316)) ([b4f4789](https://github.com/Alberto-Codes/docvet/commit/b4f47899781fa23bf84712e96ba3d5bc6b2c51f5))


### Bug Fixes

* **checks:** replace &lt;module&gt; sentinel with display names in findings ([#315](https://github.com/Alberto-Codes/docvet/issues/315)) ([6f52258](https://github.com/Alberto-Codes/docvet/commit/6f5225890a0fe71e1b76efd149f99fb6bc173468))
* **cli:** fix compute_quality key iteration and griffe guard ([3a225d3](https://github.com/Alberto-Codes/docvet/commit/3a225d31102f70f163a062b7c421bd05153dd926))


### Documentation

* **bmad:** add Growth phase PRD, architecture, and epics for Epics 31-33 ([#311](https://github.com/Alberto-Codes/docvet/issues/311)) ([8ec1abd](https://github.com/Alberto-Codes/docvet/commit/8ec1abd36ce819c09b3b9b194ff3c4a8ce50d272))

## [1.11.0](https://github.com/Alberto-Codes/docvet/compare/v1.10.0...v1.11.0) (2026-03-06)


### Features

* **enrichment:** report both doctest and rST findings for prefer-fenced-code-blocks ([#302](https://github.com/Alberto-Codes/docvet/issues/302)) ([d51edfd](https://github.com/Alberto-Codes/docvet/commit/d51edfd9e370f3d1351a318abf7f1f43b62f05a8))


### Documentation

* **site:** add Concepts page with research-backed quality narrative ([#297](https://github.com/Alberto-Codes/docvet/issues/297)) ([f88d3fc](https://github.com/Alberto-Codes/docvet/commit/f88d3fcfb4e9095fc5d6fa61471b4105a1144cd9)), closes [#296](https://github.com/Alberto-Codes/docvet/issues/296)
* **site:** expand glossary with 16 new terms and fix six-layer model ([#301](https://github.com/Alberto-Codes/docvet/issues/301)) ([f396d0c](https://github.com/Alberto-Codes/docvet/commit/f396d0c52febfa2bc97b32cff793b208e63773b0)), closes [#263](https://github.com/Alberto-Codes/docvet/issues/263)

## [1.10.0](https://github.com/Alberto-Codes/docvet/compare/v1.9.0...v1.10.0) (2026-03-06)


### Features

* **ci:** add structured inputs, annotations, and step summary to GitHub Action ([#295](https://github.com/Alberto-Codes/docvet/issues/295)) ([e932356](https://github.com/Alberto-Codes/docvet/commit/e932356a9d579e385b2458eea9decbc4aca08b2f)), closes [#294](https://github.com/Alberto-Codes/docvet/issues/294)


### Documentation

* **planning:** add Epic 30 sprint status and story artifacts ([1def643](https://github.com/Alberto-Codes/docvet/commit/1def643b0c7770b7ebbe5889c54c0346ce9f314d))
* **site:** add license attribution page and copyright footer ([#293](https://github.com/Alberto-Codes/docvet/issues/293)) ([780cb91](https://github.com/Alberto-Codes/docvet/commit/780cb912e251eab4bea14e3d2d649cd6a7e5a4b6)), closes [#292](https://github.com/Alberto-Codes/docvet/issues/292)

## [1.9.0](https://github.com/Alberto-Codes/docvet/compare/v1.8.1...v1.9.0) (2026-03-05)


### Features

* **mcp:** add guidance and fix_example to rule catalog ([#277](https://github.com/Alberto-Codes/docvet/issues/277)) ([5108e73](https://github.com/Alberto-Codes/docvet/commit/5108e732f91f6a217fc7f26ef974e70d61b55bdb))


### Bug Fixes

* **plugin:** add marketplace.json and update install instructions ([79887fa](https://github.com/Alberto-Codes/docvet/commit/79887fa6be4cf9e132d824e52894c25c19b5368e))


### Documentation

* add privacy policy page ([fa5b977](https://github.com/Alberto-Codes/docvet/commit/fa5b977d5d633aaf6e2a0ef8ec43edfedfea205b))
* **mcp:** add per-client MCP config snippets ([a4bbbbf](https://github.com/Alberto-Codes/docvet/commit/a4bbbbf7eee12eb9587aaced1213fcadf1fc3501))

## [1.8.1](https://github.com/Alberto-Codes/docvet/compare/v1.8.0...v1.8.1) (2026-03-04)


### Bug Fixes

* **mcp:** correct server.json for MCP Registry compatibility ([ca3a212](https://github.com/Alberto-Codes/docvet/commit/ca3a212208f94a4b604ac1d5f82f6174d8102c14))

## [1.8.0](https://github.com/Alberto-Codes/docvet/compare/v1.7.0...v1.8.0) (2026-03-04)


### Features

* **mcp:** add core MCP server with docvet_check and docvet_rules tools ([#261](https://github.com/Alberto-Codes/docvet/issues/261)) ([36b3dde](https://github.com/Alberto-Codes/docvet/commit/36b3dde24d1b919f59577fac3ad7aad5723cd3d9)), closes [#260](https://github.com/Alberto-Codes/docvet/issues/260)
* **mcp:** add docvet mcp CLI subcommand and integration tests ([#267](https://github.com/Alberto-Codes/docvet/issues/267)) ([c223a63](https://github.com/Alberto-Codes/docvet/commit/c223a63107b86a62c8c0f8e27629778374f8ad9e)), closes [#266](https://github.com/Alberto-Codes/docvet/issues/266)


### Bug Fixes

* **ci:** replace TestPyPI gate with local wheel smoke test ([574aa74](https://github.com/Alberto-Codes/docvet/commit/574aa74f2e167058c23830699b2f9127bcf2378c))
* **ci:** replace TestPyPI gate with local wheel smoke test ([#255](https://github.com/Alberto-Codes/docvet/issues/255)) ([574aa74](https://github.com/Alberto-Codes/docvet/commit/574aa74f2e167058c23830699b2f9127bcf2378c)), closes [#252](https://github.com/Alberto-Codes/docvet/issues/252)
* **mcp:** address code review findings for directory scoping and test ([36b3dde](https://github.com/Alberto-Codes/docvet/commit/36b3dde24d1b919f59577fac3ad7aad5723cd3d9))
* **mcp:** address code review findings for story 29.2 ([c223a63](https://github.com/Alberto-Codes/docvet/commit/c223a63107b86a62c8c0f8e27629778374f8ad9e))


### Documentation

* **mcp:** add MCP server docs, registry manifest, and version tracking ([4823bf0](https://github.com/Alberto-Codes/docvet/commit/4823bf0765087779134fbdff4f1c8c9213acefd9)), closes [#268](https://github.com/Alberto-Codes/docvet/issues/268)
* **readme:** reorder badges to industry standard convention ([574aa74](https://github.com/Alberto-Codes/docvet/commit/574aa74f2e167058c23830699b2f9127bcf2378c))

## [1.7.0](https://github.com/Alberto-Codes/docvet/compare/v1.6.4...v1.7.0) (2026-03-03)


### Features

* **presence:** add core presence detection and configuration ([#240](https://github.com/Alberto-Codes/docvet/issues/240)) ([a48edd3](https://github.com/Alberto-Codes/docvet/commit/a48edd3863674dc7a803bcdb0dff4380f9a3cc3a)), closes [#239](https://github.com/Alberto-Codes/docvet/issues/239)
* **presence:** wire presence check into CLI pipeline and reporting ([#244](https://github.com/Alberto-Codes/docvet/issues/244)) ([067fbbd](https://github.com/Alberto-Codes/docvet/commit/067fbbde52ec52638f2a413211e36ff4e3e10dd3)), closes [#243](https://github.com/Alberto-Codes/docvet/issues/243)


### Bug Fixes

* **ci:** remove unsafe-best-match index strategy from smoke test ([f7cf9d3](https://github.com/Alberto-Codes/docvet/commit/f7cf9d3353ec54fdfe81186a8205982c22dc9a9f))
* **config:** pin griffe &lt;2 for broken 2.0.0 release ([#251](https://github.com/Alberto-Codes/docvet/issues/251)) ([d408b7f](https://github.com/Alberto-Codes/docvet/commit/d408b7f80cc3dc4dbbd224850d7402c685f273cc))
* **presence:** extract PresenceStats.percentage and strengthen tests ([067fbbd](https://github.com/Alberto-Codes/docvet/commit/067fbbde52ec52638f2a413211e36ff4e3e10dd3))
* **release:** guard fromJSON with short-circuit to prevent empty parse ([#242](https://github.com/Alberto-Codes/docvet/issues/242)) ([6a944d0](https://github.com/Alberto-Codes/docvet/commit/6a944d037029e54e580b905a3d6fab62ef97ab1a))


### Documentation

* **presence:** add presence check and rule documentation with migration guide ([#249](https://github.com/Alberto-Codes/docvet/issues/249)) ([bef4fd5](https://github.com/Alberto-Codes/docvet/commit/bef4fd5c86bd04dc159cdb43934f568991f38752)), closes [#245](https://github.com/Alberto-Codes/docvet/issues/245)

## [1.6.4](https://github.com/Alberto-Codes/docvet/compare/v1.6.3...v1.6.4) (2026-03-02)


### Bug Fixes

* **ci:** add TestPyPI staging to publish pipeline ([63267ff](https://github.com/Alberto-Codes/docvet/commit/63267fff92a213b0b945c7d5fab60e6eb6f31bd4))

## [1.6.3](https://github.com/Alberto-Codes/docvet/compare/v1.6.2...v1.6.3) (2026-03-02)


### Bug Fixes

* **enrichment:** detect rST :: indented code blocks in prefer-fenced-code-blocks rule ([21e3567](https://github.com/Alberto-Codes/docvet/commit/21e35677cfbc70f63406874c8c052e16ad18a08c)), closes [#225](https://github.com/Alberto-Codes/docvet/issues/225)

## [1.6.2](https://github.com/Alberto-Codes/docvet/compare/v1.6.1...v1.6.2) (2026-03-01)


### Bug Fixes

* **cli:** replace nested ternary in _output_and_exit format resolution ([f8e7984](https://github.com/Alberto-Codes/docvet/commit/f8e798487cf99338a2c312ef94ad742ad11ebf0e)), closes [#204](https://github.com/Alberto-Codes/docvet/issues/204)

## [1.6.1](https://github.com/Alberto-Codes/docvet/compare/v1.6.0...v1.6.1) (2026-02-28)


### Bug Fixes

* **bmad:** add feature branch creation step to dev-story workflow ([a32582a](https://github.com/Alberto-Codes/docvet/commit/a32582a36664c51dbc34b1fc515e22d872423678))
* **freshness:** eliminate hunk-to-symbol false positives ([12a0314](https://github.com/Alberto-Codes/docvet/commit/12a03147537196c6c0a5fa29a05269f2e0f76482)), closes [#218](https://github.com/Alberto-Codes/docvet/issues/218)


### Documentation

* **docs:** add architecture page with Mermaid check pipeline diagram ([b9666fb](https://github.com/Alberto-Codes/docvet/commit/b9666fbf4c40e4b0f6fb9cadb29b984b44416419)), closes [#214](https://github.com/Alberto-Codes/docvet/issues/214)
* **docs:** add docs scope to commit conventions ([f7bde04](https://github.com/Alberto-Codes/docvet/commit/f7bde042f77751392c0791fa0657fe58b3e46fce)), closes [#209](https://github.com/Alberto-Codes/docvet/issues/209)
* **docs:** add editor integration page ([15a83fa](https://github.com/Alberto-Codes/docvet/commit/15a83fa18b99f391d70e303e306d9d6abc2418b3)), closes [#212](https://github.com/Alberto-Codes/docvet/issues/212)
* **docs:** fix misleading link text and zero-config claim ([15a83fa](https://github.com/Alberto-Codes/docvet/commit/15a83fa18b99f391d70e303e306d9d6abc2418b3))

## [1.6.0](https://github.com/Alberto-Codes/docvet/compare/v1.5.0...v1.6.0) (2026-02-28)


### Features

* **ci:** add cross-platform CI matrix and path normalization ([#174](https://github.com/Alberto-Codes/docvet/issues/174)) ([e418fbc](https://github.com/Alberto-Codes/docvet/commit/e418fbc670539136ae7ac0b7e3f682e9f3e40016)), closes [#101](https://github.com/Alberto-Codes/docvet/issues/101)
* **ci:** add pre-commit hook definition and tests ([#180](https://github.com/Alberto-Codes/docvet/issues/180)) ([5f11287](https://github.com/Alberto-Codes/docvet/commit/5f1128726c77311639993589f4df1419ff93cf26))
* **cli:** add --format json for structured machine-readable output ([#177](https://github.com/Alberto-Codes/docvet/issues/177)) ([da8e51d](https://github.com/Alberto-Codes/docvet/commit/da8e51d37eadb3a053052e28798192af22b1c949)), closes [#151](https://github.com/Alberto-Codes/docvet/issues/151)
* **cli:** add positional file arguments to all subcommands ([#175](https://github.com/Alberto-Codes/docvet/issues/175)) ([dee57cc](https://github.com/Alberto-Codes/docvet/commit/dee57cc40cf441f6bcb2ab322a1998c529e49fd4)), closes [#152](https://github.com/Alberto-Codes/docvet/issues/152)
* **docs:** add "How to Fix" guidance to all 19 rule pages ([#166](https://github.com/Alberto-Codes/docvet/issues/166)) ([817f43c](https://github.com/Alberto-Codes/docvet/commit/817f43c303f2220cc2e35f041027a9ad47f879a4)), closes [#155](https://github.com/Alberto-Codes/docvet/issues/155)
* **docs:** add AGENTS.md and AI Agent Integration docs page ([#171](https://github.com/Alberto-Codes/docvet/issues/171)) ([bc662a2](https://github.com/Alberto-Codes/docvet/commit/bc662a2b0215215269d37f21e3228a82b3a3baee)), closes [#161](https://github.com/Alberto-Codes/docvet/issues/161)
* **docs:** add AI Agent Integration section and enhance competitive positioning ([#170](https://github.com/Alberto-Codes/docvet/issues/170)) ([df51114](https://github.com/Alberto-Codes/docvet/commit/df511140cf19894abe8a9a4554c3ef1483771249)), closes [#153](https://github.com/Alberto-Codes/docvet/issues/153) [#162](https://github.com/Alberto-Codes/docvet/issues/162)
* **docs:** add CONTRIBUTING.md contributor guide ([#172](https://github.com/Alberto-Codes/docvet/issues/172)) ([4ff286f](https://github.com/Alberto-Codes/docvet/commit/4ff286f79ee2ed6fa831c5c175efe8fa9cff9c6c)), closes [#104](https://github.com/Alberto-Codes/docvet/issues/104)
* **lsp:** add Claude Code plugin configuration ([#185](https://github.com/Alberto-Codes/docvet/issues/185)) ([17be1f3](https://github.com/Alberto-Codes/docvet/commit/17be1f30d2136a8bc11bf6f910a733fac235608f)), closes [#63](https://github.com/Alberto-Codes/docvet/issues/63)
* **lsp:** add pygls-based LSP server for real-time diagnostics ([#184](https://github.com/Alberto-Codes/docvet/issues/184)) ([e121c38](https://github.com/Alberto-Codes/docvet/commit/e121c38c39c147bb4279f46ad2dfe93d3e391f04)), closes [#159](https://github.com/Alberto-Codes/docvet/issues/159)
* **reporting:** add format_json() for structured JSON output ([da8e51d](https://github.com/Alberto-Codes/docvet/commit/da8e51d37eadb3a053052e28798192af22b1c949))


### Bug Fixes

* **ci:** strengthen pre-commit hook YAML test assertions ([5f11287](https://github.com/Alberto-Codes/docvet/commit/5f1128726c77311639993589f4df1419ff93cf26))
* **docs:** code review fixes for AGENTS.md and ai-integration page ([bc662a2](https://github.com/Alberto-Codes/docvet/commit/bc662a2b0215215269d37f21e3228a82b3a3baee))
* **lsp:** decouple server global, narrow exception, fix handler test ([e121c38](https://github.com/Alberto-Codes/docvet/commit/e121c38c39c147bb4279f46ad2dfe93d3e391f04))


### Documentation

* **cli:** document --format json schema and usage ([da8e51d](https://github.com/Alberto-Codes/docvet/commit/da8e51d37eadb3a053052e28798192af22b1c949))
* **meta:** reserve # references for GitHub issues and PRs only ([5f11287](https://github.com/Alberto-Codes/docvet/commit/5f1128726c77311639993589f4df1419ff93cf26))

## [1.5.0](https://github.com/Alberto-Codes/docvet/compare/v1.4.0...v1.5.0) (2026-02-26)


### Features

* **cli:** add --quiet flag and dual-register --verbose on check subcommand ([#144](https://github.com/Alberto-Codes/docvet/issues/144)) ([206ab22](https://github.com/Alberto-Codes/docvet/commit/206ab22b67d16613bf3773ea3fd5734ef2ffb23c))
* **cli:** add --verbose and --quiet flags to individual subcommands ([#145](https://github.com/Alberto-Codes/docvet/issues/145)) ([ba1bbd5](https://github.com/Alberto-Codes/docvet/commit/ba1bbd55233022dfd58ad74a0d43fa41cf28b2a6))
* **cli:** replace Completed-in with Vetted summary line ([#141](https://github.com/Alberto-Codes/docvet/issues/141)) ([18db009](https://github.com/Alberto-Codes/docvet/commit/18db0098233d30daa9c29c23408f30b61e6c97a4))
* **cli:** replace Completed-in with Vetted summary line on check ([18db009](https://github.com/Alberto-Codes/docvet/commit/18db0098233d30daa9c29c23408f30b61e6c97a4))
* **config:** suppress overlap warnings for default warn-on values ([#143](https://github.com/Alberto-Codes/docvet/issues/143)) ([384a44a](https://github.com/Alberto-Codes/docvet/commit/384a44a546c10870357f16ccdfbd31ab4c9a91ba))


### Bug Fixes

* **cli:** correct --quiet flag docs and harden griffe quiet test ([#146](https://github.com/Alberto-Codes/docvet/issues/146)) ([bf1ca08](https://github.com/Alberto-Codes/docvet/commit/bf1ca088733ad1b2068f7ad7f8c9220754870508))
* **cli:** resolve verbose/quiet dual-resolution ordering in check ([206ab22](https://github.com/Alberto-Codes/docvet/commit/206ab22b67d16613bf3773ea3fd5734ef2ffb23c))
* **cli:** suppress verbose header for single-check subcommands ([ba1bbd5](https://github.com/Alberto-Codes/docvet/commit/ba1bbd55233022dfd58ad74a0d43fa41cf28b2a6))
* **config:** update overlap warning docs and strengthen AC3 test ([384a44a](https://github.com/Alberto-Codes/docvet/commit/384a44a546c10870357f16ccdfbd31ab4c9a91ba))

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
