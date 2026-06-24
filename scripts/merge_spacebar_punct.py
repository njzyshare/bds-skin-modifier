#!/usr/bin/env python3
"""
BDS 皮肤修改通用脚本 — 用于合并底行标点键到空格键

使用场景：用户希望删除底行感叹号/问号键，将空格键扩大覆盖。
通用做法：保留原始 BACK_STYLE（只改色值时才修改），只扩展 VIEW_RECT。

配置 TARGETS 和 TARGET_BS（如需改色）即可适配其他皮肤。
"""
import os, re, zipfile, shutil

# === 配置区（按需修改） ===
SRC_DIR = r"C:\Users\feijiangbin\Desktop\新建文件夹 (2)"
OUT_DIR = r"C:\Users\feijiangbin\Desktop\修改后皮肤"
TMP_DIR = r"C:\Users\feijiangbin\AppData\Local\Temp\bds_work"

TARGETS = [
    "白橙 智能深色 Amk v211228.bds",
    "灰橙 智能深色 Amk v220124.bds",
    "灰白 智能深色 Amk v211220.bds",
]

# 需要修改的 INI 文件（9键布局相关）
INI_FILES = ('py_9.ini', 'py_9_n.ini', 'def_9.ini', 'def_9_n.ini', 'bh.ini')

# 空格键新 BACK_STYLE。设为 None 则保留原始值。
# 如果原始空格键样式不对（如需要圆角），查同皮肤 26 键布局的空格键值。
TARGET_BS = 476  # 26键空格键的白色圆角值

# === 核心函数 ===

def extract(bds, d):
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    with zipfile.ZipFile(bds, 'r') as z:
        z.extractall(d)

def repack(src, outp):
    with zipfile.ZipFile(outp, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(src):
            for f in files:
                fp = os.path.join(root, f)
                z.write(fp, os.path.relpath(fp, src))

def find_key_by_center(lines, center_value):
    """通过 CENTER 值查找 KEY 编号（处理变体布局）"""
    current_key = None
    for line in lines:
        m = re.match(r'\[KEY(\d+)\]', line)
        if m:
            current_key = int(m.group(1))
        elif current_key and line.strip().startswith(f'CENTER={center_value}'):
            return current_key
    return None

def get_field(lines, key_num, field):
    """获取某个 KEY 的字段值"""
    in_target = False
    for line in lines:
        if re.match(rf'\[KEY{key_num}\]', line):
            in_target = True
        elif in_target and re.match(r'\[KEY\d+\]|\[TIP\d+\]', line):
            break
        elif in_target and line.strip().startswith(field + '='):
            return line.strip().split('=', 1)[1]
    return None

def set_field(lines, key_num, field, new_value):
    """设置某个 KEY 的字段值"""
    in_target = False
    for i, line in enumerate(lines):
        if re.match(r'\[KEY\d+\]', line):
            in_target = False
        if re.match(rf'\[KEY{key_num}\]', line):
            in_target = True
            continue
        if in_target and line.strip().startswith(field + '='):
            lines[i] = f'{field}={new_value}\r\n'
            return True
    return False

def delete_key_section(lines, key_num):
    """删除整个 [KEYnn] section"""
    start_i = end_i = None
    in_target = False
    for i, line in enumerate(lines):
        if re.match(rf'\[KEY{key_num}\]', line):
            start_i = i
            in_target = True
        elif in_target and re.match(r'\[KEY\d+\]|\[TIP\d+\]', line):
            end_i = i
            break
    if start_i is not None:
        if end_i is None:
            end_i = len(lines)
        del lines[start_i:end_i]
        return True
    return False

def process_ini(filepath, target_bs=None):
    """
    处理单个 ini 文件：
    1. 找到空格键(F38)和标点键(!/?)
    2. 计算合并后的 VIEW_RECT
    3. 更新空格键 VIEW_RECT（和可选的 BACK_STYLE）
    4. 删除标点键 sections
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # 查找空格键和标点键
    space_kn = find_key_by_center(lines, 'F38')
    if not space_kn:
        return False

    # 查找标点键（搜索 KEY14~KEY20 范围内）
    target_kns = set(range(14, 21))
    punct_kns = []
    for kn in sorted(target_kns):
        center = get_field(lines, kn, 'CENTER')
        if center and any(ch in center for ch in list('！!？?')):
            punct_kns.append(kn)

    if not punct_kns:
        return False  # 无标点键需要处理

    # 计算合并后的 VIEW_RECT
    space_rect = get_field(lines, space_kn, 'VIEW_RECT')
    if not space_rect:
        return False
    sr = tuple(int(x) for x in space_rect.split(','))

    min_x = sr[0]
    max_r = sr[0] + sr[2]
    for pk in punct_kns:
        pr = get_field(lines, pk, 'VIEW_RECT')
        if pr:
            prv = tuple(int(x) for x in pr.split(','))
            min_x = min(min_x, prv[0])
            max_r = max(max_r, prv[0] + prv[2])

    new_rect = '%d,%d,%d,%d' % (min_x, sr[1], max_r - min_x, sr[3])

    # 执行修改
    set_field(lines, space_kn, 'VIEW_RECT', new_rect)

    if target_bs is not None:
        set_field(lines, space_kn, 'BACK_STYLE', str(target_bs))

    # 删除标点键（降序避免偏移）
    for pk in sorted(punct_kns, reverse=True):
        delete_key_section(lines, pk)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    return True

def validate_no_residual(extract_dir):
    """验证无残留 !/? 键"""
    issues = []
    for root, dirs, files in os.walk(extract_dir):
        for fn in files:
            if fn not in INI_FILES:
                continue
            fp = os.path.join(root, fn)
            with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                c = f.read()
            for m in re.finditer(r'CENTER=([！!？?])', c):
                issues.append(os.path.relpath(fp, extract_dir) + ': CENTER=' + m.group(1))
    return issues

# === MAIN ===
shutil.rmtree(TMP_DIR, ignore_errors=True)
os.makedirs(OUT_DIR, exist_ok=True)

for bds_name in TARGETS:
    bds_path = os.path.join(SRC_DIR, bds_name)
    name = os.path.splitext(bds_name)[0]
    d = os.path.join(TMP_DIR, name)
    outp = os.path.join(OUT_DIR, name + '_fixed.bds')

    print('=' * 60)
    print(f'Processing: {name}')
    print('=' * 60)

    extract(bds_path, d)

    modified = False
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x != 'res']
        for fn in files:
            if fn not in INI_FILES:
                continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, d)
            if process_ini(fp, target_bs=TARGET_BS):
                modified = True
                print(f'  modified: {rel}')

    if modified:
        issues = validate_no_residual(d)
        if issues:
            print('  VALIDATION FAILED:')
            for iss in issues:
                print(f'    {iss}')
        else:
            print('  VALIDATION PASSED')
        repack(d, outp)
        print(f'  Output: {os.path.basename(outp)}')
    else:
        print('  (no changes)')

print('\nDONE')
