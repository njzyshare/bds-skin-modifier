#!/usr/bin/env python3
"""
解包并分析 BDS 文件的 KEY 布局信息。
打印每个 INI 文件中 KEY14~KEY20 的 CENTER、VIEW_RECT、BACK_STYLE。
"""
import zipfile, re, os, sys

def analyze_bds(bds_path):
    print(f'Analyzing: {os.path.basename(bds_path)}\n')
    
    with zipfile.ZipFile(bds_path, 'r') as z:
        for name in z.namelist():
            if not name.endswith(('.ini')):
                continue
            
            data = z.read(name).decode('utf-8', errors='replace')
            sections = re.split(r'(?=\[KEY\d+\])', data)
            
            print(f'--- {name} ---')
            for sec in sections:
                if not sec.startswith('[KEY'):
                    continue
                kn = re.search(r'\[KEY(\d+)\]', sec).group(1)
                center = re.search(r'CENTER=(.+)', sec)
                rect = re.search(r'VIEW_RECT=([\d,]+)', sec)
                bs = re.search(r'BACK_STYLE=(\d+)', sec)
                
                if center and rect:
                    print(f'  KEY{kn:>2s}: CENTER={center.group(1).strip():<8s} '
                          f'VIEW_RECT={rect.group(1):<15s} '
                          f'BACK_STYLE={bs.group(1) if bs else "?"}')
            print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python analyze_bds.py <bds_file1> [bds_file2 ...]')
        sys.exit(1)
    for path in sys.argv[1:]:
        if os.path.exists(path):
            analyze_bds(path)
        else:
            print(f'File not found: {path}')
