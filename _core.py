#!/usr/bin/env python3
import os, sys, math, hashlib

# Windows 控制台 UTF-8 输出（配合 bat 里的 chcp 65001）
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# ── 工具函数 ─────────────────────────────────────

def md5_of_file(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def fmt(n):
    for u in ('B','KB','MB','GB'):
        if n < 1024: return f'{n:.2f} {u}'
        n /= 1024
    return f'{n:.2f} TB'

def pause():
    input('\n按 Enter 键退出 ...')

# ── 拆分 ────────────────────────────────────────

def split_exe(src, parts=3):
    if not os.path.isfile(src):
        print(f'[错误] 找不到文件：{src}'); pause(); sys.exit(1)

    total = os.path.getsize(src)
    if total == 0:
        print('[错误] 文件为空'); pause(); sys.exit(1)

    chunk = math.ceil(total / parts)
    base  = os.path.splitext(src)[0]
    d     = os.path.dirname(src) or '.'

    print('\n---- 拆分 ----------------------------------------')
    print(f'  源文件 : {src}')
    print(f'  大小   : {fmt(total)}   每份约 {fmt(chunk)}')
    print('--------------------------------------------------')

    print('\n  计算 MD5 ...')
    orig_md5 = md5_of_file(src)
    print(f'  MD5    : {orig_md5}\n')

    names = []
    with open(src, 'rb') as f:
        for i in range(1, parts+1):
            data = f.read(chunk)
            if not data: break
            out = f'{base}.part{i}'
            with open(out, 'wb') as g: g.write(data)
            names.append(os.path.basename(out))
            print(f'  [OK] part{i}  ->  {out}  ({fmt(len(data))})')

    mf_path = os.path.join(d, f'{base}.manifest')
    with open(mf_path, 'w', encoding='utf-8') as mf:
        mf.write(f'original_filename={os.path.basename(src)}\n')
        mf.write(f'original_md5={orig_md5}\n')
        mf.write(f'parts={parts}\n')
        for n in names: mf.write(f'part={n}\n')

    print(f'\n  [OK] manifest -> {mf_path}')
    print('\n拆分完成！')
    pause()

# ── 合并 ────────────────────────────────────────

def merge_exe(part_path):
    base = part_path
    while True:
        root, ext = os.path.splitext(base)
        if ext.lower().startswith('.part'):
            base = root
        else:
            break

    d        = os.path.dirname(base) or '.'
    mf_path  = f'{base}.manifest'

    if not os.path.isfile(mf_path):
        print(f'[错误] 找不到 manifest：{mf_path}')
        print('  请确保 manifest 和分片在同一目录。')
        pause(); sys.exit(1)

    info, names = {}, []
    with open(mf_path, 'r', encoding='utf-8') as mf:
        for line in mf:
            k, _, v = line.strip().partition('=')
            if k == 'part': names.append(v)
            elif k: info[k] = v

    out_name = info.get('original_filename', os.path.basename(base)+'.exe')
    out_path = os.path.join(d, out_name)
    expected = info.get('original_md5', '')

    print('\n---- 合并 ----------------------------------------')
    print(f'  输出文件 : {out_path}')
    print(f'  分片数量 : {len(names)}')
    print('--------------------------------------------------\n')

    with open(out_path, 'wb') as dst:
        for i, name in enumerate(names, 1):
            p = os.path.join(d, name)
            if not os.path.isfile(p):
                print(f'[错误] 缺少分片：{p}'); pause(); sys.exit(1)
            with open(p, 'rb') as pf: data = pf.read()
            dst.write(data)
            print(f'  [OK] part{i}  ({fmt(len(data))})')

    if expected:
        print('\n  验证 MD5 ...')
        actual = md5_of_file(out_path)
        if actual == expected:
            print(f'  [OK] MD5 校验通过：{actual}')
        else:
            print('  [错误] MD5 不匹配，文件可能已损坏！')
            print(f'    期望：{expected}')
            print(f'    实际：{actual}')
            pause(); sys.exit(1)

    print(f'\n合并完成！-> {out_path}')
    pause()

# ── 入口 ────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        print('用法：')
        print('  把 .exe   拖到 bat 上 -> 拆成 3 份')
        print('  把 .partN 拖到 bat 上 -> 合并还原')
        pause(); return

    exe  = next((a for a in args if a.lower().endswith('.exe')),  None)
    part = next((a for a in args
                 if os.path.splitext(a)[1].lower().startswith('.part')), None)

    if exe and not part:
        split_exe(exe)
    elif part:
        merge_exe(part)
    elif exe:
        split_exe(exe)
    else:
        print(f'[错误] 不支持的文件类型：{args[0]}')
        print('  请拖入 .exe（拆分）或 .partN（合并）。')
        pause()

if __name__ == '__main__':
    main()
