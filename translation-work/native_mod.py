"""Native Tale of Immortal data-only mod packaging."""

from itertools import cycle
import io
import json
import zipfile


# Format verified against the game's examples and the original Workshop export.
# Reference: nozwock/tale-of-immortal-tool, src/EncryptTool.cs.
HEADER = bytes.fromhex("31 62 38 62 67 2d 2f 25 65 50 65 5d 50 5b 2d 2f 39 32 31 43 47")
KEY = b",.?<aH.5:.L;_=-A%K/DF4s"
MOD_ID = "YuPtBr"


def pack_resource(raw):
    return HEADER + bytes((value + key) & 255 for value, key in zip(raw, cycle(KEY)))


def unpack_resource(raw):
    if not raw.startswith(HEADER):
        raise ValueError("Cabeçalho de recurso do mod inválido")
    return bytes((value - key) & 255 for value, key in zip(memoryview(raw)[len(HEADER):], cycle(KEY)))


def mod_archive(tables):
    project = {
        "soleID": MOD_ID,
        "createTicks": 639311616000000000,
        "name": "Tale of Immortal em Português Brasileiro",
        "author": "Yuri Cunha",
        "desc": "Localização para português brasileiro. Selecione inglês no jogo.",
        "ver": "v 1.0.0",
        "autoSave": True,
        "isCreateNPC": True,
        "exportVer": 1,
        "accountID": 0,
        "publishedFileID": 0,
        "visibleState": 0,
        "openCode": 0,
        "curUpdateDesc": "",
        "tags": ["English"],
        "addPreviewPaths": [],
        "excelEncrypt": True,
    }
    prefix = f"Mod_{MOD_ID}/"
    files = {
        "ModExportData.cache": {"projectData": project, "items": {}, "modNamespace": None},
        **{f"ModExcel/{table}.json": rows for table, rows in tables.items() if rows},
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, value in files.items():
            raw = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            archive.writestr(zipfile.ZipInfo(prefix + name), pack_resource(raw),
                             compress_type=zipfile.ZIP_DEFLATED)
    return output.getvalue()
