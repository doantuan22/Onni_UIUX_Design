# UI Engineering Plugin v0.1.0 Release Notes

**Release Date:** 2026-09-26  
**Status:** RELEASE-READY (Local & Package Verified)  
**Release Tag:** `v0.1.0`  
**Distribution Archive:** `ui-ux-design-0.1.0.zip`

---

## Highlights

UI Engineering Plugin v0.1.0 provides an AI coding agent pair-programming system dedicated to UI engineering, frontend modernizations, and component design without hallucination.

- **Unified Shared Core:** One shared engine (`plugins/ui-engineering/`) housing all skills, 261 design & domain knowledge entries, workflows, and tools.
- **Thin Platform Adapters:** Zero-copy thin adapters for Claude Code (`.claude-plugin/`), OpenAI Codex (`.codex-plugin/`), and generic Model Context Protocol (MCP) environments.
- **Controlled Modification Planning:** "Preserve First, Improve Second, Redesign Only When Explicitly Requested" invariant engine with strict semantic negation, brand protection, and palette locking.
- **Runtime Critique & Repair:** Headless visual/DOM inspection, empty-evidence gating, and diagnostic validation with automated repair planning.
- **Self-Contained & Reproducible:** Zero external source-tree dependencies upon installation; package checksums and deterministic build output.

---

## Compatibility Matrix

| Platform / Host | Adapter Path | Support Status | Capabilities Exposed |
|---|---|---|---|
| **Claude Code** | `.claude-plugin/` | SUPPORTED (Integration Verified) | 24 public tools, commands, skills |
| **OpenAI Codex** | `.codex-plugin/` | SUPPORTED (Integration Verified) | 24 public tools, capabilities |
| **Generic CLI / Python** | `python -m uiux.cli` | SUPPORTED | All 24 tools, self-test, verify |
| **MCP stdio Transport** | `uiux.adapters.mcp` | SUPPORTED | `initialize`, `tools.list`, `tools.call` |

*Note on Host Execution:* Host execution tests are verified via platform metadata and synthetic adapter integration checks. When a physical host daemon (e.g. proprietary Claude/Codex client) is absent from the build environment, verification status is marked `ADAPTER_INTEGRATION_VERIFIED; HOST_EXECUTION_BLOCKED` rather than faked.

---

## Known Limitations & Runtime Environment

### Browser Runtime Qualification: `BLOCKED_BROWSER_RUNTIME`
- The plugin includes headless Playwright verification (`runtime_critic`, `recapture`, visual inspection).
- In environments without installed Playwright browser binaries (e.g., standard minimal CI containers or developer machines without `playwright install`), browser-dependent checks will report `BLOCKED_BROWSER_RUNTIME`.
- **Policy Compliance:** The plugin strictly adheres to the **No Auto-Install Policy**. It will **never** automatically download browser binaries or invoke package managers in user projects. Provisioning browser binaries is the sole responsibility of the host environment or explicit CI workflow configuration.

---

## Installation & Upgrade

### Install via GitHub Source
```bash
git clone https://github.com/doantuan22/Onni_UIUX_Design.git
cd Onni_UIUX_Design
python plugins/ui-engineering/scripts/uiux_cli.py call self_test
```

### Install from Packaged Release Archive
1. Download `ui-ux-design-0.1.0.zip` and its SHA-256 checksum from the GitHub Releases page.
2. Unzip into your project's plugin directory or a global plugin root:
   ```bash
   unzip ui-ux-design-0.1.0.zip -d ~/.plugins/ui-engineering
   ```
3. Verify integrity:
   ```bash
   python -m uiux.cli --plugin-dir ~/.plugins/ui-engineering self_test
   ```

### Upgrading
To upgrade an existing installation:
1. Replace the plugin directory with the new release version.
2. Run `python -m uiux.cli self_test` to confirm all 24 public tools and 261 knowledge items are active.
3. No user project files are modified during an upgrade.

---

## Rollback Policy
If an upgrade causes incompatibilities with an existing host environment:
1. Delete or rename the updated plugin directory.
2. Extract the previous release archive (e.g., `ui-engineering-0.0.9.zip`).
3. Re-run `python -m uiux.cli self_test`.
4. The plugin maintains backward compatibility across minor releases for all public CLI and tool arguments.

---

## Verification Summary
- **Unit & Integration Suite:** 528 / 528 PASS
- **Packaging Verifier:** 43 / 43 PASS (13 validation stages: syntax, schemas, manifests, adapters, dependencies, clean-scratch test execution)
- **Self-Test Suite:** 9 / 9 PASS
- **Adapter Thinness Check:** 100% PASS (Zero duplicate skills, knowledge, or runtime scripts)
