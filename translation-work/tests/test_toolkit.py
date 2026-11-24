import contextlib
import hashlib
import subprocess
import zipfile
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import toolkit


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "fixture"
        self.source.mkdir()

    def seed(self, count=2):
        self.tables = {
            "LocalText": [
                {"id": str(index), "key": f"k{index}", "en": "Value {0}", "ch": "", "tc": ""}
                for index in range(count)
            ],
            "RoleLogLocal": [
                {"id": str(index), "keyID": "same", "en": "Value {0}", "ch": "", "tc": ""}
                for index in range(2)
            ],
            "BattleSkillPrefixName": [{"id": "1", "text": "", "en": "Prefix", "tc": ""}],
        }
        self.write_tables()

    def write_tables(self):
        for name, rows in self.tables.items():
            raw = toolkit.encode(rows).encode("utf-8")
            (self.source / f"{name}.json").write_bytes(b"\xef\xbb\xbf" + raw + b"\r\n")

    def sync(self, dry=False):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            toolkit.update_sources(self.root, self.source, dry)
        return json.loads(output.getvalue())

    def payload(self, index, translation):
        source = self.tables["LocalText"][index]
        row = {
            "id": f"LocalText/{source['key']}",
            "revision": toolkit.revision("LocalText", source),
            "ptbr": translation,
        }
        path = self.root / "payload.jsonl"
        path.write_text(toolkit.encode(row) + "\n", encoding="utf-8")
        return path

    def test_revision_changes_are_local_and_old_source_is_recoverable(self):
        self.seed()
        self.assertEqual(self.sync(True), {"added": 5})
        self.assertFalse((self.root / "translation-work").exists())
        self.sync()
        toolkit.apply(self.root, 1, self.payload(0, "Valor {0}"), False)
        toolkit.apply(self.root, 1, self.payload(1, "Valor {0}"), False)
        old_source = dict(self.tables["LocalText"][0])
        self.tables["LocalText"][0]["en"] = "New value {0}"
        self.write_tables()
        self.assertEqual(self.sync(True)["changed"], ["LocalText/k0"])
        self.assertEqual(self.sync()["changed"], ["LocalText/k0"])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            toolkit.check(self.root)
            toolkit.check(self.root, resume=True)
            toolkit.inspect(self.root, None, None, "LocalText/k0")
        summary, resumed, history = map(json.loads, output.getvalue().splitlines())
        self.assertEqual(summary, {"stale": 1, "approved": 1, "pending": 3})
        self.assertEqual(resumed, {**summary, "next_batch": 1})
        self.assertEqual(history, old_source)
        self.assertEqual(self.sync(), {"added": [], "changed": [], "removed": [], "restored": []})

    def test_invalid_update_and_payload_preserve_accepted_state(self):
        self.seed()
        self.sync()
        toolkit.apply(self.root, 1, self.payload(0, "Valor {0}"), False)
        with self.assertRaisesRegex(ValueError, "Marcadores"):
            toolkit.apply(self.root, 1, self.payload(1, "Valor"), False)
        with self.assertRaisesRegex(ValueError, "Tradução anterior"):
            toolkit.apply(self.root, 1, self.payload(0, "Outro {0}"), False)
        self.tables["LocalText"].append(self.tables["LocalText"][0])
        self.write_tables()
        with self.assertRaisesRegex(ValueError, "identidade|Identidade"):
            self.sync()
        self.assertEqual(set(toolkit.approved(self.root, 1)), {"LocalText/k0"})

    def test_complete_editor_build_preserves_other_fields_and_rejects_tampering(self):
        self.seed()
        self.sync()
        target = self.root / "translation-work/local/editor-input.zip"
        with self.assertRaisesRegex(ValueError, "incompleta"):
            toolkit.build_editor(self.root)
        with self.assertRaisesRegex(ValueError, "incompleta"):
            toolkit.build_editor(self.root, native=True)
        mod = target.with_name("PTBR.zip")
        self.assertFalse(mod.exists())
        self.assertFalse(target.exists())
        records = []
        for table in toolkit.TABLES:
            for identity, row in toolkit.table_rows(table, (self.source / f"{table}.json").read_bytes()):
                records.append({"id": identity, "revision": toolkit.revision(table, row), "ptbr": row["en"]})
        records[0]["ptbr"] = "Valor {0}"
        records[2]["ptbr"] = "Registro {0}"
        records[-1]["ptbr"] = "Prefixo"
        payload = self.root / "payload.jsonl"
        payload.write_text("\n".join(map(toolkit.encode, records)), encoding="utf-8")
        toolkit.apply(self.root, 1, payload, False)
        with contextlib.redirect_stdout(io.StringIO()):
            toolkit.build_editor(self.root)
            toolkit.build_editor(self.root, native=True)
        before = target.read_bytes()
        with zipfile.ZipFile(target) as archive:
            self.assertEqual(set(archive.namelist()), {f"ModExcel/{table}.json" for table in toolkit.TABLES})
            untouched = (self.source / "RoleLogLocal.json").read_bytes()
            self.assertEqual(toolkit.rewrite_table("RoleLogLocal", untouched, {}), untouched)
            result = toolkit.decode(archive.read("ModExcel/LocalText.json"))
            self.assertEqual(result[0], dict(self.tables["LocalText"][0], en="Valor {0}"))
            self.assertEqual(result[1], self.tables["LocalText"][1])
        with zipfile.ZipFile(mod) as archive:
            prefix = "Mod_YuPtBr/"
            self.assertEqual(set(archive.namelist()), {prefix + "ModExportData.cache"} |
                             {prefix + f"ModExcel/{table}.json" for table in toolkit.TABLES})
            metadata = toolkit.decode(toolkit.unpack_resource(archive.read(prefix + "ModExportData.cache")))
            self.assertEqual(metadata["projectData"]["soleID"], "YuPtBr")
            self.assertTrue(metadata["projectData"]["excelEncrypt"])
            expected = {
                "LocalText": [{"id": "0", "key": "k0", "en": "Valor {0}"}],
                "RoleLogLocal": [{"id": "0", "en": "Registro {0}"}],
                "BattleSkillPrefixName": [{"id": "1", "en": "Prefixo"}],
            }
            for table, rows in expected.items():
                raw = archive.read(prefix + f"ModExcel/{table}.json")
                self.assertEqual(toolkit.decode(toolkit.unpack_resource(raw)), rows)
        with contextlib.closing(toolkit.database(self.root, create=True)) as db:
            db.execute("UPDATE sources SET raw = ? WHERE name = 'RoleLogLocal'", (untouched + b" ",))
            db.commit()
        with self.assertRaisesRegex(ValueError, "Checksum"):
            toolkit.build_editor(self.root)
        self.assertEqual(target.read_bytes(), before)

    def test_500_applies_touch_only_the_target_batch(self):
        self.seed(50_000)
        self.sync()
        update_dir = self.root / "translation-work/translations"
        for batch in range(1, 101):
            toolkit.apply(self.root, batch, self.payload((batch - 1) * 500, "Valor {0}"), False)
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in update_dir.glob("*.jsonl")}
        for number in range(500):
            toolkit.apply(self.root, 1, self.payload(0, f"Valor {number} {{0}}"), True)
        after = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in update_dir.iterdir()}
        self.assertEqual(set(before), set(after))
        self.assertEqual({name for name in before if before[name] != after[name]}, {"batch-0001.jsonl"})
        self.assertLess(sum(len(raw) for raw, _ in after.values()), 20_000)

    def test_canonical_git_bytes_and_tampering(self):
        script = toolkit.ROOT / "translation-work/toolkit.py"
        canonical = script.read_bytes()
        fixture = self.root / "translation-work"
        fixture.mkdir()
        modified = fixture / script.name
        modified.write_bytes(canonical.replace(b"\n", b"\r\n"))
        codec = script.with_name("native_mod.py")
        (fixture / codec.name).write_bytes(codec.read_bytes().replace(b"\n", b"\r\n"))
        receipt = fixture / "toolchain.json"
        receipt.write_bytes((script.parent / receipt.name).read_bytes())
        git_blob = subprocess.run(
            ["git", "hash-object", "--path=translation-work/toolkit.py", "--stdin"],
            input=modified.read_bytes(), cwd=toolkit.ROOT, capture_output=True, check=True,
        ).stdout.decode().strip()
        expected_blob = hashlib.sha1(f"blob {len(canonical)}\0".encode() + canonical).hexdigest()
        self.assertEqual(git_blob, expected_blob)
        with patch.object(toolkit, "ROOT", self.root):
            with contextlib.redirect_stdout(io.StringIO()):
                toolkit.doctor(False)
            modified.write_bytes(canonical + b"\n# alteration\n")
            with self.assertRaisesRegex(ValueError, "Checksum"):
                toolkit.doctor(False)

    def test_steam_detection_refuses_wrong_ambiguous_and_incomplete_installs(self):
        def fixture(name, app_id="1468810", complete=True):
            steamapps = self.root / name / "steamapps"
            install = steamapps / "common/Tale of Immortal"
            reference = install / toolkit.REFERENCE
            reference.mkdir(parents=True)
            (steamapps / "appmanifest_1468810.acf").write_text(
                f'  "appid" "{app_id}"\n  "installdir" "Tale of Immortal"\n', encoding="utf-8",
            )
            for filename in ("guigubahuang.exe", "GameAssembly.dll"):
                (install / filename).touch()
            if complete:
                for table in toolkit.TABLES:
                    (reference / f"{table}.json").touch()
            return steamapps, install

        wrong, _ = fixture("Wrong ID", app_id="123")
        with self.assertRaisesRegex(ValueError, "--source-dir"):
            toolkit.discover_game([wrong])
        correct, install = fixture("Main Steam Library")
        self.assertEqual(toolkit.discover_game([correct, correct, wrong]), install)
        duplicate, _ = fixture("Duplicate")
        with self.assertRaisesRegex(ValueError, "ambígua"):
            toolkit.discover_game([correct, duplicate])
        incomplete, _ = fixture("Incomplete", complete=False)
        with self.assertRaisesRegex(ValueError, "incompleta"):
            toolkit.discover_game([correct, incomplete])

    def test_preflight_read_only(self):
        with contextlib.redirect_stdout(io.StringIO()):
            toolkit.doctor(False)
        self.assertEqual(list(self.root.iterdir()), [self.source])


if __name__ == "__main__":
    unittest.main()
