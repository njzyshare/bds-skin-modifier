# 自检排错工作流

## 背景

处理 BDS 皮肤修改时，你无法直接看到修改后的视觉效果（无法在手机上即时测试）。必须通过**数据推理**来替代目测——预测修改后的效果，然后验证。

本文档记录了一套系统化的自检排错方法，来自今天从 V7 到 V23 的教训。

---

## 第一步：确认原始状态

用户提出任何"不对"时，**第一步永远是从原始 BDS 文件读取数据**，不要相信任何中间文件。

```python
def check_original_value(bds_path, ini_path, key_num, field):
    """从原始 BDS 读取某个 KEY 的字段值"""
    import zipfile, re
    
    with zipfile.ZipFile(bds_path, 'r') as z:
        data = z.read(ini_path).decode('utf-8', errors='replace')
        lines = data.split('\n')
        
        in_target = False
        for line in lines:
            if re.match(rf'\[KEY{key_num}\]', line):
                in_target = True
            elif in_target and re.match(r'\[KEY\d+\]|\[TIP\d+\]', line):
                break
            elif in_target and line.strip().startswith(field + '='):
                return line.strip().split('=', 1)[1]
    return None
```

**为什么要从原始 BDS 读？**
- 修改过的中间文件可能已经被多次修改，你不知道哪一步改坏了
- 原始 BDS 是唯一的"地真"（ground truth）

## 第二步：对比改前改后

将原始值与修改后的值放在一起对比：

```
原始：KEY16 BACK_STYLE=354  VIEW_RECT=398,433,278,140
修改：KEY16 BACK_STYLE=476  VIEW_RECT=305,433,464,140
```

**检查清单**：
1. ✅ 修改了期望的 KEY（不是其他 KEY）
2. ✅ 修改了期望的字段（不是其他字段）
3. ✅ 新值正确（不是拼写错误或计算错误）
4. ✅ 其他字段原样保留（没有被意外修改）

## 第三步：坐标可视化推理

当你修改了键的尺寸和位置后，用"纸面推演"预测效果：

```
键盘宽度假设为 1080px（竖屏）

底行键（y≈433）：
KEY14(F6):  x=0,     w=93    → 右侧边界 93
KEY15(F16): x=93,    w=93    → 右侧边界 186
KEY16(F38): x=305,   w=464   → 右侧边界 769  ← 空格
KEY19(F1):  x=769,   w=93    → 右侧边界 862
KEY20(F39): x=862,   w=93    → 右侧边界 955
```

**关键验证点**：
- 同一行的 y 值应该一致（底行所有键 y≈433）
- 相邻键的边界应该对齐（KEY16 右边界 ≈ KEY19 左边界）
- 底行总宽度应该填充键盘宽度

## 第四步：BACK_STYLE 值推理

修改 BACK_STYLE 时，通过分析同皮肤内的其他键来验证新值是否合理：

```python
def analyze_back_style(bds_path):
    """分析 BDS 中所有 BACK_STYLE 值对应的键"""
    import zipfile, re
    
    bs_map = {}
    with zipfile.ZipFile(bds_path, 'r') as z:
        for name in z.namelist():
            if not name.endswith('.ini'):
                continue
            data = z.read(name).decode('utf-8', errors='replace')
            sections = re.split(r'(?=\[KEY\d+\])', data)
            for sec in sections:
                if not sec.startswith('[KEY'):
                    continue
                bs = re.search(r'BACK_STYLE=(\d+)', sec)
                ct = re.search(r'CENTER=(.+)', sec)
                if bs and ct:
                    bs_map.setdefault(bs.group(1), []).append(ct.group(1).strip())
    
    # 输出分析
    for bs in sorted(bs_map.keys(), key=int):
        centers = list(set(bs_map[bs]))[:8]
        print(f'BACK_STYLE={bs}: 出现在 {centers}')
```

**推理规则**：
- 空格键(F38)应该和同类键（如 26 键空格）用相同值
- 功能键(F6/F16/F1)通常用相同值（灰色功能区）
- 字母键通常用相同值（白色小圆角）
- 如果空格键改成了某个值，验证该值是否用于白色键

## 第五步：跨布局交叉验证

同一个皮肤的不同布局文件是互相印证的关键：

```python
def cross_check(bds_path):
    """跨布局验证"""
    import zipfile, re
    
    with zipfile.ZipFile(bds_path, 'r') as z:
        for name in z.namelist():
            if not ('py_9' in name or 'py_26' in name or 'en_9' in name):
                continue
            if not name.endswith('.ini'):
                continue
            data = z.read(name).decode('utf-8', errors='replace')
            
            # 找空格键(F38)
            m = re.search(r'\[KEY(\d+)\][^\[]*?CENTER=F38[^\[]*?(?=\[|$)', data, re.DOTALL)
            if m:
                bs = re.search(r'BACK_STYLE=(\d+)', m.group(0))
                print(f'{name}: space=KEY{m.group(1)}, BACK_STYLE={bs.group(1) if bs else "?"}')
```

**验证点**：
- py_9.ini 和 py_26.ini 的空格键 BACK_STYLE 应该一致（同皮肤）
- en_9.ini 的空格键 BACK_STYLE 也应该是同类值

## 第六步：分层排查法

当用户说"不对"时，按以下顺序排查：

```
1. 读文件确认当前值
   → 用 get_field() 从输出文件读，确认值是什么
  
2. 对比原始值
   → 从原始 BDS 读，确认原始值是什么
  
3. 如果当前值 ≠ 原始值：
   → 是哪一步修改引入的？
   → 是否是预期的修改？
   
4. 如果修改是预期内的但效果不对：
   → 这个新值在其他皮肤中表现如何？
   → 有没有其他键使用同样的值？
   → 这个值在 main.png 中对应什么区域？
   
5. 提出修复方案
   → 列出候选值
   → 给出推理依据
   → 执行修改 → 验证
```

## 典型场景排查速查表

| 现象 | 可能原因 | 排查方法 |
|------|---------|---------|
| 空格颜色变了 | BACK_STYLE 被改了 | 对比原始值 |
| 空格圆角不对 | BACK_STYLE 不是圆角值 | 找 26 键空格值 |
| !/? 没删掉 | 脚本没处理到该文件 | 验证所有 INI 文件 |
| 相邻键错位 | VIEW_RECT 计算错误 | 坐标连续性检查 |
| 某文件没改到 | 文件不在遍历范围内 | 检查 INI_FILES 列表 |
| dark 对了 light 不对 | light 和 dark 结构不同 | 对比两者目录结构 |
