"""UI map (map_ui_structure / diff_ui_maps): markup parser, section mapping, roles, banlist signals, map diffs.

The Next.js + Tailwind fixture in development/fixtures/targets/target-c-next-tailwind is deliberately generic
("AI look"); tests load it into memory so they also run from an extracted artifact when the fixture is present.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import _paths
from uiux import api
from uiux.engine.ui_map import build_ui_map, diff_ui_maps, render_markdown
from uiux.engine.ui_map.markup import class_string, parse_source, walk

FIXTURE = _paths.REPO_ROOT / "development/fixtures/targets/target-c-next-tailwind"


def _fixture_files() -> dict[str, str]:
    return {p.relative_to(FIXTURE).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(FIXTURE.rglob("*")) if p.is_file()}


def _map(contents: dict[str, str], **options) -> dict:
    import json
    return build_ui_map(".", dict(options, files=sorted(contents), file_contents=contents,
                                  package_json=json.loads(contents.get("package.json", "{}"))))


def _elements(roots):
    return [n for n, _ in walk(roots) if n.get("type") == "element"]


class MarkupParserTests(unittest.TestCase):
    def test_jsx_tree_with_lists_conditionals_and_ts_generics(self) -> None:
        src = """
        const x: Array<string> = [];
        function id<T,>(a: T) { return a < 3 ? a : a }
        export default function Page({ items }: Props) {
          const [s] = useState<string>("");
          // <NotJsx />
          return (
            <main className="flex">
              <h1>Don't stop</h1>
              {items.map((it) => <Card key={it.id} className={cn("rounded-xl", s && "p-4")} title={it.title} />)}
              {s ? <p>Yes</p> : null}
              <>
                <a href="/x">Go &amp; see</a>
              </>
            </main>
          );
        }
        """
        parsed = parse_source(src, "tsx")
        self.assertEqual([c["name"] for c in parsed["components"]], ["Page"])
        tags = [(n["tag"], n["repeated"], n["conditional"]) for n in _elements(parsed["roots"])]
        self.assertEqual(tags, [("main", False, False), ("h1", False, False), ("Card", True, False),
                                ("p", False, True), ("", False, False), ("a", False, False)])
        card = _elements(parsed["roots"])[2]
        self.assertEqual(class_string(card), "rounded-xl p-4")
        texts = [n["text"] for n, _ in walk(parsed["roots"]) if n.get("type") == "text"]
        self.assertIn("Don't stop", texts)
        self.assertIn("Go & see", texts)

    def test_templates_vue_svelte_html(self) -> None:
        vue = parse_source('<template><div class="a"><h1>{{ title }}</h1><img src="x.png"><p>Hi</div></template>'
                           '<script setup>import Hero from "./Hero.vue"</script>', "vue")
        self.assertEqual([n["tag"] for n in _elements(vue["roots"])], ["div", "h1", "img", "p"])
        svelte = parse_source('<script>let items = []</script><section>{#each items as i}<li>{i}</li>{/each}</section>',
                              "svelte")
        self.assertEqual([n["tag"] for n in _elements(svelte["roots"])], ["section", "li"])
        html = parse_source("<!doctype html><html><body><nav><a href='/'>Home</a></nav><br><main><p>x</main>"
                            "<script>if (a < b) {}</script></body></html>", "html")
        self.assertEqual([n["tag"] for n in _elements(html["roots"])],
                         ["html", "body", "nav", "a", "br", "main", "p"])

    def test_malformed_input_degrades_without_raising(self) -> None:
        for src in ("return (<div><span>", "<<<>>>{{{", "const a = <"):
            self.assertIsInstance(parse_source(src, "tsx")["roots"], list)


@unittest.skipUnless(FIXTURE.is_dir(), "fixture is repository-only")
class FixtureMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.files = _fixture_files()
        cls.map = _map(cls.files)
        cls.home = next(r for r in cls.map["routes"] if r["path"] == "/")

    def test_routes_shell_and_section_order(self) -> None:
        self.assertEqual(self.map["framework"], "nextjs")
        self.assertEqual([r["path"] for r in self.map["routes"]], ["/", "/pricing"])
        self.assertEqual(self.home["layouts"], ["src/app/layout.tsx"])
        shell = self.map["shell"][0]
        self.assertTrue(shell["has_slot"])
        self.assertEqual([(e["role"], e["component"]) for e in shell["before_slot"]], [("navigation", "Navbar")])
        self.assertEqual([(e["role"], e["component"]) for e in shell["after_slot"]], [("footer", "Footer")])
        self.assertEqual([s["role"] for s in self.home["sections"]],
                         ["hero", "social-proof", "features", "pricing", "testimonials", "faq", "cta"])
        self.assertEqual(self.home["sections"][2]["file"], "src/components/features.tsx")

    def test_content_inventory_and_fingerprint(self) -> None:
        hero = self.home["sections"][0]
        self.assertEqual(hero["content"]["headings"][0], {"level": 1, "text": "Unlock the power of seamless automation"})
        self.assertEqual([a["label"] for a in hero["content"]["actions"]], ["Start free trial", "Book a demo"])
        self.assertIn("h1:unlock the power of seamless automation", self.home["fingerprint"])
        self.assertIn("action:start free trial", self.home["fingerprint"])
        pricing = self.home["sections"][3]
        self.assertTrue(pricing["content"]["repeated"])
        self.assertIn("equal cards", pricing["pattern"]["summary"])

    def test_banlist_signals_and_density(self) -> None:
        hero_hits = {h["id"] for h in self.home["sections"][0]["banlist"]}
        for item in ("purple-gradient", "gradient-text", "blur-blobs", "centered-hero", "hover-scale", "hype-copy",
                     "round-number-stats", "low-contrast-body"):
            self.assertIn(item, hero_hits)
        feature_hits = {h["id"] for h in self.home["sections"][2]["banlist"]}
        self.assertTrue({"equal-icon-cards", "uniform-radius-shadow"} <= feature_hits)
        self.assertEqual({h["id"] for h in self.home["page_banlist"]}, {"centered-everything", "uniform-rhythm"})
        self.assertEqual(self.home["generic_density"]["level"], "high")
        self.assertIn("/", self.map["summary"]["high_density_routes"])

    def test_tokens_in_use(self) -> None:
        used = self.map["tokens"]["used"]
        self.assertEqual(used["dominant_hues"][0], "indigo")
        self.assertIn("shadow-lg", used["shadows"])
        self.assertTrue(any("Inter" in f for f in used["declared_fonts"]))

    def test_markdown_inventory(self) -> None:
        md = render_markdown(self.map)
        self.assertIn("Shell `src/app/layout.tsx`: navigation:Navbar → {page} → footer:Footer", md)
        self.assertIn("| 1 | hero | centered", md)

    def test_diff_detects_recomposition_and_resolved_signals(self) -> None:
        after = dict(self.files)
        after["src/components/hero.tsx"] = '''import Link from "next/link";
import Image from "next/image";

export function Hero() {
  return (
    <section className="mx-auto grid max-w-7xl gap-12 px-6 pt-20 lg:grid-cols-12 lg:items-end">
      <div className="lg:col-span-7">
        <p className="font-mono text-xs uppercase tracking-widest text-indigo-700">New: AI workflows</p>
        <h1 className="mt-6 text-6xl font-semibold tracking-tight">Unlock the power of seamless automation</h1>
        <p className="mt-4 max-w-xl text-lg text-gray-700">Flowbase connects your tools so your team ships faster.</p>
        <div className="mt-8 flex gap-4">
          <Link href="/signup" className="bg-indigo-700 px-6 py-3 text-white">Start free trial</Link>
          <Link href="/demo" className="border px-6 py-3">Book a demo</Link>
        </div>
        <p className="mt-6 text-sm">10k+ teams · 99.9% uptime · 24/7 support</p>
      </div>
      <Image src="/product.png" alt="Flowbase run history" width={1200} height={800} className="lg:col-span-5 lg:-mr-24" />
    </section>
  );
}
'''
        for name in ("logo-cloud", "pricing", "testimonials", "faq", "cta"):
            path = f"src/components/{name}.tsx"
            after[path] = after[path].replace('className="py-24 text-center"',
                                              'className="mx-auto grid max-w-7xl gap-10 py-20 lg:grid-cols-12"')
        diff = diff_ui_maps(self.map, _map(after))
        home = next(r for r in diff["routes"] if r["path"] == "/")
        self.assertTrue(diff["content_preserved"], home["content_removed"])
        self.assertGreaterEqual(home["sections_recomposed"], 5)
        self.assertTrue(diff["elevate_bar"]["met"])
        self.assertTrue({"purple-gradient", "blur-blobs", "centered-hero", "centered-everything"}
                        <= set(home["banlist_resolved"]))

    def test_diff_flags_content_loss(self) -> None:
        after = dict(self.files)
        after["src/app/page.tsx"] = after["src/app/page.tsx"].replace("      <Faq />\n", "")
        diff = diff_ui_maps(self.map, _map(after))
        self.assertFalse(diff["content_preserved"])
        self.assertFalse(diff["elevate_bar"]["met"])
        home = next(r for r in diff["routes"] if r["path"] == "/")
        self.assertIn("h2:frequently asked questions", home["content_removed"])

    def test_tool_surface(self) -> None:
        result = api.call_tool("map_ui_structure", {"project": str(FIXTURE), "options": {"markdown": True,
                                                                                         "detail": "summary"}})
        self.assertIn("## Section inventory", result["markdown"])
        self.assertEqual(result["summary"]["routes_mapped"], 2)
        same = api.call_tool("diff_ui_maps", {"before": result, "after": result})
        self.assertTrue(same["content_preserved"])
        self.assertEqual(same["recomposition_ratio"], 0.0)
        self.assertFalse(same["elevate_bar"]["met"])


class SpaAndTemplateMapTests(unittest.TestCase):
    def test_react_router_spa(self) -> None:
        files = {
            "package.json": '{"dependencies": {"react": "18.0.0", "react-dom": "18.0.0", "react-router-dom": "6.0.0"}}',
            "src/main.tsx": 'import App from "./App";\ncreateRoot(el).render(<App />);\n',
            "src/App.tsx": '''import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import About from "./pages/About";
import { Header } from "./components/Header";
export default function App() {
  return (
    <div className="min-h-screen">
      <Header />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </div>
  );
}
''',
            "src/components/Header.tsx": 'export function Header() { return <header><nav><a href="/">Home</a><a href="/about">About</a></nav></header>; }\n',
            "src/pages/Home.tsx": '''export default function Home() {
  return (
    <>
      <section className="py-16"><h1>Welcome</h1><button>Sign up</button></section>
      <section id="team"><h2>Our team</h2><p>Small and focused.</p></section>
    </>
  );
}
''',
            "src/pages/About.tsx": 'export default function About() { return <main><h1>About us</h1><p>Since 2020.</p></main>; }\n',
        }
        ui = _map(files)
        self.assertEqual([r["path"] for r in ui["routes"]], ["/", "/about"])
        home = ui["routes"][0]
        self.assertEqual(home["file"], "src/pages/Home.tsx")
        self.assertEqual([s["role"] for s in home["sections"]], ["hero", "team"])
        self.assertEqual(ui["shell"][0]["before_slot"][0]["role"], "navigation")
        self.assertTrue(ui["shell"][0]["has_slot"])

    def test_static_html_page(self) -> None:
        files = {"index.html": "<html><body><header><nav><a href='/'>Home</a></nav></header><main>"
                               "<section class='hero'><h1>Hello</h1><a href='#start'>Start</a></section>"
                               "<section id='faq'><h2>FAQ</h2><details><summary>Q</summary><p>A</p></details></section>"
                               "</main><footer><p>© 2026</p></footer></body></html>"}
        ui = _map(files)
        self.assertEqual([s["role"] for s in ui["routes"][0]["sections"]], ["navigation", "hero", "faq", "footer"])


if __name__ == "__main__":
    unittest.main()
