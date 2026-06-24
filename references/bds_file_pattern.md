# BDS INI 文件过滤与遍历策略

## INI 文件列表

修改 BDS 时需遍历的 INI 文件模式：

| 文件名 | 用途 | 一般需要修改 |
|--------|------|-------------|
| `py_9.ini` | 拼音 9 键布局 | ✅ 是 |
| `def_9.ini` | 默认 9 键布局 | ✅ 是 |
| `bh.ini` | 手写 9 键布局 | ✅ 是 |
| `py_9_n.ini` | 拼音 9 键夜间模式 | ✅ 是 |
| `def_9_n.ini` | 默认 9 键夜间模式 | ✅ 是 |
| `py_26.ini` | 拼音 26 键布局 | ❌ 通常不（布局不同） |
| `en_9.ini` | 英文 9 键布局 | ❌ 通常不（英文键盘） |
| `en_9_n.ini` | 英文 9 键夜间 | ❌ 通常不 |
| `hw_full.ini` | 全键盘手写 | ❌ 通常不（布局不同） |

## 目录遍历逻辑

```python
INI_FILES = ('py_9.ini', 'py_9_n.ini', 'def_9.ini', 'def_9_n.ini', 'bh.ini')

for root, dirs, files in os.walk(extract_dir):
    dirs[:] = [x for x in dirs if x != 'res']  # 跳过 res/ 目录
    for fn in files:
        if fn not in INI_FILES:
            continue
        filepath = os.path.join(root, fn)
        # process file
```

注意：`res/` 目录包含 `main.png` 等素材文件，不需要修改。

## 变体布局注意事项

某些皮肤在 `light/port/py_9.ini` 中的键顺序与标准布局不同（如灰橙）。**永远不要假设 KEY16 就是空格键**，应通过 CENTER=F38 动态查找。
