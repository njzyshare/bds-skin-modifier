

<p align="center">
  <strong>BDS Skin Modifier</strong>
  <br />
  <em>百度输入法 BDS 皮肤修改工具 — 键位调整 · 样式修改 · 批量处理</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License" />
  <img src="https://img.shields.io/badge/python-3.8+-green" alt="Python 3.8+" />
</p>

---

## 简介

BDS Skin Modifier 是一个百度输入法 BDS 皮肤文件修改工具集。通过解析和修改 BDS 文件中的 INI 布局配置，实现对键盘键位、样式、布局的自由调整。

**典型场景：**
- 合并底行感叹号/问号键到空格键（让空格更长）
- 调整键的大小和位置
- 修改键的视觉样式（圆角、颜色）
- 处理多主题（深色/浅色）和多方向（横屏/竖屏）布局

## 功能

- ✅ **批量处理** — 一次性处理多个 BDS 皮肤
- ✅ **键位合并** — 合并相邻按键，自动计算新尺寸
- ✅ **键位删除** — 删除不需要的按键
- ✅ **样式修改** — 修改 BACK_STYLE 改变键的视觉效果
- ✅ **变体布局** — 自动适应不同皮肤的按键编号差异
- ✅ **多主题覆盖** — 同时处理 dark/light 主题、land/port 方向
- ✅ **自动验证** — 修改后自动检查残留和错误

## 开始使用

### 安装

```bash
# 安装依赖（如果你要直接运行 Python 脚本）
pip install zipfile36
```

### 快速上手

```bash
# 1. 分析一个 BDS 皮肤，查看键位布局
python scripts/analyze_bds.py "白橙 智能深色 Amk v211228.bds"

# 2. 编辑 merge_spacebar_punct.py 中的 TARGETS 列表
# 改为你要处理的皮肤文件路径

# 3. 运行合并脚本
python scripts/merge_spacebar_punct.py
```

### 工作流

```
1. 解包 BDS  →  2. 分析 INI 结构  →  3. 执行修改  →  4. 验证  →  5. 打包 BDS
```

每个步骤的详细说明见 `references/` 目录。

## 项目结构

```
bds-skin-modifier/
├── SKILL.md                        # 主干工作流（AI 助手加载的入口）
├── scripts/
│   ├── analyze_bds.py              # 分析 BDS，打印 KEY 布局
│   └── merge_spacebar_punct.py     # 合并底行标点键到空格（通用模板）
├── references/
│   ├── ini_modification_general.md # 逐行解析操作方法集
│   ├── self_check_flow.md          # 自检排错工作流
│   ├── back_style_notes.md         # BACK_STYLE 值分析经验
│   ├── bds_file_pattern.md         # INI 文件过滤模式
│   └── key_center_dict.json        # CENTER 功能码映射字典
└── .gitignore
```

## BDS 文件结构

BDS 文件本质是 ZIP 压缩包，内部按主题/方向/布局划分：

```
皮肤.bds
├── dark/               # 深色主题
│   ├── land/           # 横屏
│   │   ├── py_9.ini    # 拼音 9 键
│   │   ├── def_9.ini   # 默认 9 键
│   │   ├── bh.ini      # 手写
│   │   ├── py_26.ini   # 26 键
│   │   └── en_9.ini    # 英文 9 键
│   ├── port/           # 竖屏（结构同上）
│   └── res/main.png    # 皮肤素材图
├── light/              # 浅色主题（结构同上）
└── ...
```

## INI 配置说明

每个 `.ini` 文件包含多个 `[KEYnn]` section，控制按键的行为和外观：

```ini
[KEY16]
CENTER=F38                    ; 键功能：F38=空格, F39=回车, F1=发送
VIEW_RECT=398,433,278,140     ; 位置大小：x,y,宽度,高度
BACK_STYLE=354                ; 背景样式编号（指向 main.png 的区域）
FORE_STYLE=305                ; 前景/文字样式编号
```

## 使用技巧

### 找到正确的 BACK_STYLE

修改键的视觉样式时，同皮肤的不同布局文件可以互相参考：

```python
# 查 26 键布局的空格键样式
# py_26.ini 中 CENTER=F38 的 BACK_STYLE 通常是白色圆角值
```

详见 `references/back_style_notes.md`。

### 处理变体布局

某些皮肤的特定 INI 文件按键编号顺序不同，通过 CENTER 值动态查找，不硬编码 KEY 编号：

```python
def find_key_by_center(lines, 'F38'):  # 查找空格键
```

## 常见问题

**Q: 修改后空格颜色变了？**
A: 检查是否误改了 BACK_STYLE。如果原始样式不对，参考 26 键布局的空格 BACK_STYLE 值。

**Q: 某个文件没被处理到？**
A: 检查 `merge_spacebar_punct.py` 中的 `INI_FILES` 列表是否包含该文件名。

**Q: dark 对了 light 不对？**
A: 两个主题目录结构可能不同，需要分别确认。

## License

MIT
