"""把本仓库的 mod 发布到实际运行的那份安装目录（避免「改了仓库、游戏里没变」）。

用法：python mod/publish.py [目标 mod 目录]
不给参数时读 mod/settings.local.json 的 install_path。"""
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent


def target_dir():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    cfg = ROOT / "settings.local.json"
    if cfg.exists():
        data = json.loads(cfg.read_text(encoding="utf-8"))
        if data.get("install_path"):
            return Path(data["install_path"])
    return None


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    dst = target_dir()
    if not dst or not dst.exists():
        raise SystemExit("找不到目标目录；请传入参数或在 settings.local.json 写 install_path")
    print("源：", ROOT)
    print("目标：", dst)
    copied = 0
    for src in sorted((ROOT / "payload").rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(ROOT)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists() or sha(src) != sha(out):
            shutil.copy2(src, out)
            copied += 1
    for name in ("WitE2CN.exe", "WitE2CN_Text.dll"):
        s = ROOT / name
        if s.exists():
            o = dst / name
            if not o.exists() or sha(s) != sha(o):
                shutil.copy2(s, o)
                copied += 1
    for name in ("README.md",):
        s = ROOT / name
        if s.exists():
            shutil.copy2(s, dst / name)
    pkg = json.loads((dst / "payload" / "package.json").read_text(encoding="utf-8"))
    ok = all(sha(dst / rel) == h for rel, h in json.loads((dst / "payload" / "checksums.json").read_text(encoding="utf-8")).items())
    print("复制文件：", copied)
    print("目标版本：", pkg.get("mod_version"), "条目：", pkg.get("translations"))
    print("校验：", "通过" if ok else "失败")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()