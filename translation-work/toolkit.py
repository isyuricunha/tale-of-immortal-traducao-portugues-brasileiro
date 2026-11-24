"""Local workflow for the three Tale of Immortal reference localization tables."""

import argparse
from collections import Counter
from contextlib import closing
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import sqlite3
import sys
import tempfile
import zipfile

from native_mod import mod_archive, unpack_resource

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = Path("Mod/modFQA/配置修改教程/配置（只读）Json格式")
TABLES = {"LocalText": "key", "RoleLogLocal": "id", "BattleSkillPrefixName": "id"}
TOKEN = re.compile(r"\{[^{}\r\n]+\}|</?[a-zA-Z][^<>\r\n]*>|%[0-9]*\$?[sdif]")
BATCH_SIZE = 500


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Campo JSON duplicado: {key}")
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_object)


def table_rows(table, raw):
    records = decode(raw)
    if not isinstance(records, list) or not records:
        raise ValueError(f"Tabela inválida ou vazia: {table}")
    identities = set()
    for row in records:
        required = {"id", "en", "tc", TABLES[table]}
        required.add("text" if table == "BattleSkillPrefixName" else "ch")
        if table == "RoleLogLocal":
            required.add("keyID")
        if not isinstance(row, dict) or not required <= row.keys():
            raise ValueError(f"Linha sem os campos esperados em {table}")
        if not all(isinstance(value, str) for value in row.values()):
            raise ValueError(f"Valor não textual em {table}/{row['id']}")
        identity = row[TABLES[table]]
        if not identity or identity in identities:
            raise ValueError(f"Identidade vazia ou repetida em {table}: {identity}")
        identities.add(identity)
        yield f"{table}/{identity}", row


def revision(table, row):
    ignored = {"kr"}
    if table == "LocalText":
        ignored.add("id")
    context = {key: row[key] for key in sorted(row) if key not in ignored}
    return digest(encode(context).encode("utf-8"))


def source_text(row):
    return next((row[key] for key in ("en", "ch", "text", "tc")
                 if row.get(key, "").strip()), "")


def validate_text(original, translation):
    if not isinstance(translation, str) or not translation.strip():
        raise ValueError("Tradução vazia ou inválida")
    translation.encode("utf-8")
    if "\x00" in translation or Counter(TOKEN.findall(original)) != Counter(TOKEN.findall(translation)):
        raise ValueError("Marcadores ou tags incompatíveis")


def ensure_game(path):
    if not (path / "guigubahuang.exe").is_file() or not (path / "GameAssembly.dll").is_file():
        raise ValueError(f"Instalação Windows de Tale of Immortal não reconhecida: {path}")
    return path / REFERENCE


def steam_roots():
    roots = [parent.parent for parent in (Path.cwd(), *Path.cwd().parents)
             if parent.name.lower() == "common" and parent.parent.name.lower() == "steamapps"]
    if sys.platform == "win32":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                steam = Path(winreg.QueryValueEx(key, "SteamPath")[0])
        except OSError:
            return roots
        roots.append(steam / "steamapps")
        libraries = steam / "steamapps/libraryfolders.vdf"
        if libraries.is_file():
            for entry in re.findall(r'^\s*"path"\s+"([^"]+)"',
                                    libraries.read_text(encoding="utf-8-sig"), re.MULTILINE):
                roots.append(Path(entry.replace("\\\\", "\\")) / "steamapps")
    return roots


def discover_game(libraries):
    candidates = set()
    incomplete = set()
    for library in {path.resolve() for path in libraries}:
        manifest = library / "appmanifest_1468810.acf"
        if not manifest.is_file():
            continue
        contents = manifest.read_text(encoding="utf-8-sig")
        app_ids = re.findall(r'^\s*"appid"\s+"([^"]+)"', contents, re.MULTILINE)
        folders = re.findall(r'^\s*"installdir"\s+"([^"]+)"', contents, re.MULTILINE)
        if app_ids != ["1468810"] or len(folders) != 1 or re.search(r'[\\/:]', folders[0]):
            continue
        common = (library / "common").resolve()
        install = (common / folders[0]).resolve()
        if install.parent != common:
            continue
        try:
            reference = ensure_game(install)
            if not all((reference / f"{table}.json").is_file() for table in TABLES):
                raise ValueError("Inventário de referência incompleto")
        except ValueError:
            incomplete.add(install)
        else:
            candidates.add(install)
    if len(candidates) == 1 and not incomplete:
        return next(iter(candidates))
    if candidates or incomplete:
        paths = ", ".join(str(path) for path in sorted(candidates | incomplete))
        raise ValueError(f"Instalação Steam ambígua ou incompleta ({paths}). Informe --game-root.")
    raise ValueError("Instalação Steam não encontrada. Informe --game-root ou --source-dir.")


def database(root, create=False, require_existing=False):
    path = root / "translation-work/local/state.sqlite3"
    if (not create or require_existing) and not path.is_file():
        raise ValueError("Base ausente. Execute update-sources primeiro.")
    if require_existing:
        return sqlite3.connect(path.as_uri() + "?mode=rw", uri=True)
    if not create:
        return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


def update_sources(root, source, dry_run):
    incoming = {}
    for table in TABLES:
        raw = (source / (table + ".json")).read_bytes()
        rows = list(table_rows(table, raw))
        incoming[table] = (raw, rows)
    connection_path = root / "translation-work/local/state.sqlite3"
    if dry_run and not connection_path.is_file():
        print(encode({"added": sum(len(rows) for _, rows in incoming.values())}))
        return
    with closing(database(root, create=not dry_run)) as db:
        if not dry_run:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS sources (name TEXT PRIMARY KEY, raw BLOB NOT NULL);
                CREATE TABLE IF NOT EXISTS source_receipts (name TEXT PRIMARY KEY, sha256 TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS entries (
                    identity TEXT PRIMARY KEY, revision TEXT NOT NULL,
                    batch INTEGER NOT NULL, row TEXT NOT NULL, active INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS entries_batch ON entries(batch, active);
                CREATE TABLE IF NOT EXISTS history (
                    identity TEXT NOT NULL, revision TEXT NOT NULL, row TEXT NOT NULL,
                    PRIMARY KEY (identity, revision)
                );
            """)
            db.execute("BEGIN IMMEDIATE")
        else:
            db.execute("BEGIN")
        accepted_sources = read_sources(db, incoming if not dry_run else None)
        previous = {row[0]: row[1:] for row in db.execute(
            "SELECT identity, revision, batch, row, active FROM entries"
        )}
        next_position = len(previous)
        seen = set()
        diff = {"added": [], "changed": [], "removed": [], "restored": []}
        for table, (raw, rows) in incoming.items():
            for identity, row in rows:
                seen.add(identity)
                signature = revision(table, row)
                old = previous.get(identity)
                serialized = encode(row)
                if old is None:
                    batch = next_position // BATCH_SIZE + 1
                    next_position += 1
                    diff["added"].append(identity)
                else:
                    batch = old[1]
                    if not old[3]:
                        diff["restored"].append(identity)
                    if signature != old[0]:
                        diff["changed"].append(identity)
                        if not dry_run:
                            db.execute("INSERT OR IGNORE INTO history VALUES (?, ?, ?)",
                                       (identity, old[0], old[2]))
                    if (signature, batch, serialized, 1) == old:
                        continue
                if not dry_run:
                    db.execute("INSERT OR REPLACE INTO entries VALUES (?, ?, ?, ?, 1)",
                               (identity, signature, batch, serialized))
            if not dry_run and accepted_sources.get(table) != raw:
                db.execute("INSERT OR REPLACE INTO sources VALUES (?, ?)", (table, raw))
                db.execute("INSERT OR REPLACE INTO source_receipts VALUES (?, ?)", (table, digest(raw)))
        diff["removed"] = sorted(identity for identity in previous.keys() - seen if previous[identity][3])
        if not dry_run:
            db.executemany("UPDATE entries SET active = 0 WHERE identity = ?",
                           ((identity,) for identity in diff["removed"]))
            db.commit()
        print(encode(diff))


def read_sources(db, incoming=None):
    sources = dict(db.execute("SELECT name, raw FROM sources"))
    receipts = dict(db.execute("SELECT name, sha256 FROM source_receipts"))
    if receipts.keys() - sources.keys():
        raise ValueError("Recibo sem tabela de origem")
    for name, raw in sources.items():
        fingerprint = digest(raw)
        if name not in receipts and incoming and name in incoming and incoming[name][0] == raw:
            db.execute("INSERT INTO source_receipts VALUES (?, ?)", (name, fingerprint))
        elif receipts.get(name) != fingerprint:
            raise ValueError(f"Checksum da tabela de origem divergente: {name}")
    return sources


def legacy_candidates(path):
    candidates = {}
    for table in TABLES:
        raw = (path / (table + ".json")).read_bytes()
        for identity, row in table_rows(table, raw):
            candidates[identity] = row
    return candidates


def approved(root, batch):
    path = root / f"translation-work/translations/batch-{batch:04}.jsonl"
    return read_payload(path) if path.exists() else {}


def read_payload(path):
    records = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        row = json.loads(line, object_pairs_hook=unique_object)
        if not isinstance(row, dict) or set(row) != {"id", "revision", "ptbr"}:
            raise ValueError(f"Linha {number}: use apenas id, revision e ptbr")
        if not all(isinstance(value, str) for value in row.values()) or row["id"] in records:
            raise ValueError(f"Linha {number}: campos inválidos ou ID duplicado")
        records[row["id"]] = row
    return records


def apply(root, batch, payload, overwrite):
    if batch < 1:
        raise ValueError("Número de lote inválido")
    updates = read_payload(payload)
    if not updates:
        raise ValueError("Payload vazio")
    with closing(database(root, create=True, require_existing=True)) as db:
        db.execute("BEGIN IMMEDIATE")
        rows = {identity: (signature, json.loads(raw)) for identity, signature, raw in db.execute(
            "SELECT identity, revision, row FROM entries WHERE active = 1 AND batch = ?", (batch,)
        )}
        current = approved(root, batch)
        merged = dict(current)
        for identity, record in updates.items():
            if identity not in rows or record["revision"] != rows[identity][0]:
                raise ValueError(f"ID fora do lote ou revisão desatualizada: {identity}")
            validate_text(source_text(rows[identity][1]), record["ptbr"])
            previous = current.get(identity)
            if previous and previous != record and not overwrite:
                raise ValueError(f"Tradução anterior presente: {identity}. Use --overwrite após revisar.")
            merged[identity] = record
        if merged == current:
            return
        target = root / f"translation-work/translations/batch-{batch:04}.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=target.parent, delete=False) as request:
            temporary = Path(request.name)
            try:
                for identity in sorted(merged):
                    request.write(encode(merged[identity]) + "\n")
                request.flush()
                os.fsync(request.fileno())
            except BaseException:
                request.close()
                temporary.unlink()
                raise
        try:
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)


def translation_state(root, db):
    report = Counter()
    batches = {}
    translations = {}
    next_batch = None
    for identity, signature, batch, raw, active in db.execute(
        "SELECT identity, revision, batch, row, active FROM entries"
    ):
        if batch not in batches:
            batches[batch] = approved(root, batch)
        record = batches[batch].pop(identity, None)
        if not active:
            report["removed"] += 1
        elif not source_text(json.loads(raw)) and record is None:
            report["empty_source"] += 1
        elif record is None:
            report["pending"] += 1
            next_batch = batch if next_batch is None else min(batch, next_batch)
        elif record["revision"] != signature:
            report["stale"] += 1
            next_batch = batch if next_batch is None else min(batch, next_batch)
        else:
            validate_text(source_text(json.loads(raw)), record["ptbr"])
            translations[identity] = record["ptbr"]
            report["approved"] += 1
    expected = {f"batch-{number:04}.jsonl" for number in batches}
    present = {path.name for path in (root / "translation-work/translations").glob("*.jsonl")}
    if present - expected:
        raise ValueError("Há arquivos de tradução sem lote de origem")
    if any(batches.values()):
        raise ValueError("Há traduções com IDs desconhecidos ou no lote incorreto")
    return report, translations, next_batch


def check(root, resume=False):
    with closing(database(root)) as db:
        db.execute("BEGIN")
        report, _, next_batch = translation_state(root, db)
        result = dict(report)
        if resume:
            result["next_batch"] = next_batch
        print(encode(result))


def rewrite_table(table, raw, translations):
    rows = []
    changed = False
    for identity, row in table_rows(table, raw):
        if identity in translations and row["en"] != translations[identity]:
            row["en"] = translations[identity]
            changed = True
        rows.append(row)
    if not changed:
        return raw
    indent = 2
    newline = "\r\n" if b"\r\n" in raw else "\n"
    contents = json.dumps(rows, ensure_ascii=False, indent=indent).replace("\n", newline)
    if raw.endswith(b"\n"):
        contents += newline
    prefix = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    return prefix + contents.encode("utf-8")


def build_editor(root, native=False):
    with closing(database(root, create=True, require_existing=True)) as db:
        db.execute("BEGIN IMMEDIATE")
        report, translations, _ = translation_state(root, db)
        if report["pending"] or report["stale"]:
            raise ValueError(f"Tradução incompleta: {report['pending']} pendentes, {report['stale']} desatualizadas")
        sources = read_sources(db)
        if set(sources) != set(TABLES):
            raise ValueError("Inventário das tabelas incompleto")
        expected = set(translations)
        seen = {identity for table, raw in sources.items() for identity, _ in table_rows(table, raw)}
        if not expected <= seen:
            raise ValueError("Há traduções sem correspondência na origem")
        filename = "PTBR.zip" if native else "editor-input.zip"
        target = root / "translation-work/local" / filename
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as staging:
            temporary = Path(staging.name)
        try:
            if native:
                tables = {}
                for table, raw in sources.items():
                    rows = []
                    for identity, row in table_rows(table, raw):
                        if identity not in translations or translations[identity] == row["en"]:
                            continue
                        override = {"id": row["id"], "en": translations[identity]}
                        if table == "LocalText":
                            override["key"] = row["key"]
                        rows.append(override)
                    tables[table] = rows
                if not any(tables.values()):
                    raise ValueError("Nenhuma substituição para o mod")
                temporary.write_bytes(mod_archive(tables))
            else:
                with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                    for table in TABLES:
                        entry = zipfile.ZipInfo(f"ModExcel/{table}.json")
                        archive.writestr(entry, rewrite_table(table, sources[table], translations),
                                         compress_type=zipfile.ZIP_DEFLATED)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        print(target)


def inspect(root, batch, legacy, history):
    with closing(database(root)) as db:
        if history:
            for (row,) in db.execute("SELECT row FROM history WHERE identity = ?", (history,)):
                print(row)
            return
        if batch is None:
            for number, total in db.execute(
                "SELECT batch, count(*) FROM entries WHERE active = 1 GROUP BY batch ORDER BY batch"
            ):
                print(encode({"batch": number, "active": total}))
            return
        legacy_rows = legacy_candidates(legacy) if legacy else {}
        accepted = approved(root, batch)
        for identity, signature, raw in db.execute(
            "SELECT identity, revision, row FROM entries WHERE active = 1 AND batch = ? ORDER BY rowid",
            (batch,),
        ):
            row = json.loads(raw)
            previous = legacy_rows.get(identity)
            record = {"id": identity, "revision": signature, "source": row, "ptbr": None}
            saved = accepted.get(identity)
            if saved:
                if saved["revision"] == signature:
                    record["ptbr"] = saved["ptbr"]
                else:
                    record["previous_approval"] = saved
            if previous and previous["en"] != row["en"]:
                record["legacy_review"] = previous
            print(encode(record))


def doctor(require_arm64):
    architecture = platform.machine().lower()
    if require_arm64 and (sys.platform != "linux" or architecture not in ("aarch64", "arm64")):
        raise ValueError(f"Arquitetura/sistema incompatível: {architecture}/{sys.platform}")
    receipt = decode((ROOT / "translation-work/toolchain.json").read_bytes())
    if set(receipt) != {"toolkit.py", "native_mod.py"}:
        raise ValueError("Inventário do toolkit inválido")
    for name, expected in receipt.items():
        actual = (ROOT / "translation-work" / name).read_bytes().replace(b"\r\n", b"\n")
        if digest(actual) != expected:
            raise ValueError(f"Checksum do toolkit divergente: {name}")
    raw = b'\xef\xbb\xbf[{"id":"1","key":"example","en":"Value {0}","ch":"","tc":""}]\r\n'
    [(identity, row)] = list(table_rows("LocalText", raw))
    validate_text(row["en"], "Valor {0}")
    with closing(sqlite3.connect(":memory:")) as db:
        db.execute("CREATE TABLE fixture (id TEXT, raw BLOB)")
        db.execute("INSERT INTO fixture VALUES (?, ?)", (identity, raw))
        stored = db.execute("SELECT raw FROM fixture").fetchone()[0]
    rebuilt = rewrite_table("LocalText", stored, {identity: "Valor {0}"})
    row["en"] = "Valor {0}"
    if stored != raw or list(table_rows("LocalText", rebuilt))[0][1] != row:
        raise ValueError("Falha na fixture de leitura e preservação de bytes")
    with zipfile.ZipFile(io.BytesIO(mod_archive({"LocalText": [row]}))) as archive:
        resource = next(name for name in archive.namelist() if name.endswith("/LocalText.json"))
        if decode(unpack_resource(archive.read(resource))) != [row]:
            raise ValueError("Falha na fixture de empacotamento de mod")
    print(f"OK: Python {platform.python_version()}, SQLite {sqlite3.sqlite_version}, {architecture}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    source = commands.add_parser("update-sources")
    location = source.add_mutually_exclusive_group()
    location.add_argument("--game-root", type=Path)
    location.add_argument("--source-dir", type=Path)
    source.add_argument("--dry-run", action="store_true")
    commands.add_parser("status")
    commands.add_parser("check")
    commands.add_parser("resume")
    commands.add_parser("build-editor")
    commands.add_parser("build-mod")
    changes = commands.add_parser("apply")
    changes.add_argument("number", type=int)
    changes.add_argument("payload", type=Path)
    changes.add_argument("--overwrite", action="store_true")
    batch = commands.add_parser("batch")
    batch.add_argument("number", type=int)
    batch.add_argument("--legacy-modexcel", type=Path)
    history = commands.add_parser("history")
    history.add_argument("id")
    preflight = commands.add_parser("doctor")
    preflight.add_argument("--require-arm64", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "update-sources":
            directory = args.source_dir or ensure_game(args.game_root or discover_game(steam_roots()))
            update_sources(ROOT, directory, args.dry_run)
        elif args.command == "apply":
            apply(ROOT, args.number, args.payload, args.overwrite)
        elif args.command in ("check", "resume"):
            check(ROOT, resume=args.command == "resume")
        elif args.command in ("build-editor", "build-mod"):
            build_editor(ROOT, native=args.command == "build-mod")
        elif args.command == "doctor":
            doctor(args.require_arm64)
        else:
            inspect(ROOT, getattr(args, "number", None), getattr(args, "legacy_modexcel", None),
                    getattr(args, "id", None))
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Erro: {error}\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    main()
