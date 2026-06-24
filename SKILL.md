---
name: bds-skin-modifier
description: >
  百度输入法 BDS 皮肤文件修改工具。
  适用于键位调整、样式修改、布局变体处理等各种修改需求。
---

# BDS 皮肤修改 Skill

## 文件结构

BDS 是 ZIP 压缩包，内部结构：

```
[皮肤名].bds
├── dark/light → land/port → *.ini + res/main.png
```

INI 文件由 `[KEYnn]` section 组成，关键字段：
- `CENTER`：键功能（F38=空格，F39=回车，F1=发送，F6=符号，等等）
- `VIEW_RECT=x,y,w,h`：位置和大小
- `BACK_STYLE=num`：背景样式编号（指向 `main.png`）

## 主干工作流

```
解包 BDS → 分析 INI 结构 → 执行修改 → 验证 → 打包 BDS
```

### 解包与分析

```python
import zipfile, os
with zipfile.ZipFile(bds_path, 'r') as z:
    z.extractall(extract_dir)
```

**全局扫描**：遍历所有 `.ini`，不预设只改哪些。通过 `CENTER` 动态查找目标键，不硬编码 KEY 编号。检查所有主题（dark/light）×方向（land/port）。改前先全局摸清结构，不受影响的文件也要知道它们存在。

### 修改 INI

逐行解析（不用正则跨 section 匹配），保留 `\r\n` 格式。详见 `references/ini_modification_general.md`。

### 验证

修改后必须验证（详见 `references/self_check_flow.md`）。

### 打包

```python
with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(source_dir):
        for f in files:
            z.write(os.path.join(root, f), os.path.relpath(os.path.join(root,f), source_dir))
```

## 自检原则

1. **先诊断再动手** — 改前读、改后验（三明治法则）
2. **先读后写** — 只读分析先做，可逆修改后做
3. **固定排错顺序** — 复现→对比→推理→修复→验证
4. **数据推理替代目测** — 坐标连贯性、跨布局对比、BACK_STYLE 关联性

详见 `references/self_check_flow.md`。

## 工具脚本

- `scripts/analyze_bds.py` — 分析 BDS 打印 KEY 布局
- `scripts/merge_spacebar_punct.py` — 合并底行标点键到空格（通用，可配置）

## 参考资料

- `references/key_center_dict.json` — CENTER 功能码映射
- `references/back_style_notes.md` — BACK_STYLE 值分析经验
- `references/bds_file_pattern.md` — INI 文件过滤模式
- `references/ini_modification_general.md` — 逐行解析操作集
- `references/self_check_flow.md` — 自检排错工作流
