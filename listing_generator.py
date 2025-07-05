#!/usr/bin/env python3
"""
listing_generator.py

Генерация полного листинга исходников в plain-text для AI-промта.
"""

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    import pathspec
    _HAS_PATHSPEC = True
except ImportError:
    _HAS_PATHSPEC = False


def load_config(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def load_gitignore(root):
    gitignore = os.path.join(root, '.gitignore')
    if not os.path.isfile(gitignore):
        return []
    patterns = []
    for line in open(gitignore, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        patterns.append(line)
    return patterns


def build_pathspec(root, patterns):
    # если установлен pathspec (рекомендуется для полного .gitignore-парсинга)
    spec = pathspec.PathSpec.from_lines(
        pathspec.patterns.GitWildMatchPattern,
        patterns
    )
    return spec


def is_excluded(rel_path, spec, extra_patterns):
    # 1) нормализуем разделители в POSIX-стиль
    rel = rel_path.replace(os.sep, '/')
    # 2) убираем ровно префикс "./", если он есть
    if rel.startswith('./'):
        rel = rel[2:]

    # 3) правила из .gitignore (через pathspec)
    if spec and spec.match_file(rel):
        return True

    # 4) собственные шаблоны из конфига
    for pat in extra_patterns:
        # тоже в POSIX-стиль
        p = pat.replace(os.sep, '/')

        if p.endswith('/'):
            # паттерн на директорию (включая любые вложения)
            dir_pat = p.rstrip('/')
            if rel == dir_pat or rel.startswith(dir_pat + '/'):
                return True
        else:
            # обычный файл/путь
            if fnmatch.fnmatch(rel, p):
                return True

    return False

def should_skip_file(filename: str, text: str, cfg: dict) -> bool:
    """Возвращает True, если файл надо исключить из листинга
       (пустой или тривиальный __init__.py)."""
    # --- пустые вообще ---
    if cfg.get('skip_empty') and not text.strip():
        return True

    # --- тривиальные __init__.py ---
    if cfg.get('skip_trivial_inits') and filename == '__init__.py':
        # убираем пустые и комментарии
        significant = [
            ln for ln in text.splitlines()
            if ln.strip() and not ln.lstrip().startswith('#')
        ]
        # сколько «осмысленных» строк допускаем
        limit = cfg.get('trivial_init_max_noncomment', 1)
        if len(significant) <= limit:
            # все ли эти строки — простые заглушки?
            if all(ln.strip() in ('pass', '...') for ln in significant):
                return True
    return False

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        '-c', '--config',
        default='docs.listing_config.json',
        help='Путь к файлу конфига (JSON)'
    )
    p.add_argument(
        '--mode',
        choices=('all', 'changes'),
        default='all',
        help='all = обход всего проекта; changes = только изменённые в Git файлы'
    )
    args = p.parse_args()

    cfg_path = os.path.abspath(args.config)
    root = os.path.dirname(cfg_path)
    os.chdir(root)

    cfg = load_config(cfg_path)
    exts = {e.lower() for e in cfg.get('extensions', ['.py'])}
    extra_ignore = cfg.get('exclude', [])

    gitignore_patterns = load_gitignore(root)
    all_patterns = gitignore_patterns  # для pathspec
    if _HAS_PATHSPEC:
        spec = build_pathspec(root, all_patterns)
    else:
        spec = None

    # имя этого скрипта, чтобы не включать его в листинг
    script_name = os.path.basename(__file__)

    # ------------------------------------------------------------
    # ➊ Собираем список файлов, если выбран режим "changes"
    # ------------------------------------------------------------
    changed_files: set[str] | None = None
    if args.mode == 'changes':
        changed_files = set()

        def _git(names: list[str]) -> list[str]:
            return subprocess.check_output(
                ['git', '-C', root, *names],
                text=True, encoding='utf-8', errors='ignore'
            ).splitlines()

        # 1) unstaged
        changed_files.update(_git(['diff', '--name-only']))
        # 2) staged (index)
        changed_files.update(_git(['diff', '--name-only', '--cached']))
        # 3) новые/неотслеживаемые
        changed_files.update(_git(['ls-files', '--others', '--exclude-standard']))

        # нормализуем к POSIX-пути
        changed_files = {Path(p).as_posix() for p in changed_files if p}

    # ------------------------------------------------------------
    # ➋ Обходим дерево
    # ------------------------------------------------------------
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        # пропускаем .git и сами себя
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir in ('.git', './.git'):
            dirnames[:] = []
            continue

        # фильтруем сабдиректории (чтобы не заходить в __pycache__ и т.п.)
        dirnames[:] = [
            d for d in dirnames
            if not is_excluded(os.path.join(rel_dir, d), spec, extra_ignore)
        ]

        for fn in filenames:
            # пропускаем сам скрипт генерации
            if fn == script_name:
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext not in exts:
                continue
            rel_file = os.path.normpath(os.path.join(rel_dir, fn))
            if is_excluded(rel_file, spec, extra_ignore):
                continue

            # если включён режим CHANGES — сразу отсеиваем чужие файлы
            if changed_files is not None:
                rel_posix = Path(rel_file).as_posix()
                if rel_posix not in changed_files:
                    continue

            full = os.path.join(root, rel_file)
            with open(full, encoding='utf-8') as f:
                content = f.read()

            # 5) игнорируем пустые / тривиальные файлы
            if should_skip_file(fn, content, cfg):
                continue

            # преобразовать в UNIX-стиль ("/")
            rel_unix = rel_file.replace(os.sep, '/').lstrip('./')
            out.append(f"# —— FILE: {rel_unix} ——\n")
            out.append(content)
            out.append("\n\n")

    sys.stdout.write(''.join(out))


if __name__ == '__main__':
    main()
