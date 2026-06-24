# INI 逐行解析通用操作方法集

## 为什么必须逐行解析

BDS 的 INI 文件由多个 `[KEYnn]` section 组成，用正则跨 section 匹配很容易出错：

```python
# ❌ 错误做法：跨 section 匹配
re.search(r'\[KEY(\d+)\].*?CENTER=F38', content, re.DOTALL)
# 可能匹配到 KEY1 中某个恰好包含 F38 的字段
```

## 正确做法：逐行解析

### 1. 收集 KEY 信息

```python
def collect_key_info(lines):
    """收集文件中所有 KEY 的信息"""
    key_info = {}  # kn -> {'center':..., 'rect':..., 'bs':..., 'start_line':.., 'end_line':..}
    current_key = None
    
    for i, line in enumerate(lines):
        m = re.match(r'\[KEY(\d+)\]', line)
        if m:
            if current_key is not None:
                key_info[current_key]['end_line'] = i
            current_key = int(m.group(1))
            key_info[current_key] = {'start_line': i, 'end_line': None}
            continue
        
        if current_key is not None:
            s = line.strip()
            if s.startswith('CENTER='):
                key_info[current_key]['center'] = s.split('=', 1)[1]
            elif s.startswith('VIEW_RECT='):
                key_info[current_key]['rect'] = s.split('=', 1)[1]
            elif s.startswith('BACK_STYLE='):
                key_info[current_key]['bs'] = s.split('=', 1)[1]
            elif s.startswith('FORE_STYLE='):
                key_info[current_key]['fs'] = s.split('=', 1)[1]
    
    # 最后一个 KEY 到文件尾
    if current_key is not None and key_info[current_key]['end_line'] is None:
        key_info[current_key]['end_line'] = len(lines)
    
    return key_info
```

### 2. 修改 KEY 字段

```python
def set_field(lines, key_num, field, new_value):
    """设置 KEYnn 的 field=value"""
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
```

### 3. 批量修改多个字段

```python
def set_fields(lines, key_num, fields_dict):
    """批量设置 KEYnn 的多个字段
    fields_dict = {'VIEW_RECT': '100,200,300,140', 'BACK_STYLE': '476'}
    """
    in_target = False
    for i, line in enumerate(lines):
        if re.match(r'\[KEY\d+\]', line):
            in_target = False
        if re.match(rf'\[KEY{key_num}\]', line):
            in_target = True
            continue
        if in_target:
            s = line.strip()
            for field, new_val in fields_dict.items():
                if s.startswith(field + '='):
                    lines[i] = f'{field}={new_val}\r\n'
                    break  # 一行只匹配一个字段
    return True
```

### 4. 获取 KEY 字段值

```python
def get_field(lines, key_num, field):
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

### 5. 删除 KEY section

```python
def delete_key_section(lines, key_num):
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
```

### 6. 查找 KEY 编号（动态）

```python
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
```

### 7. 计算 VIEW_RECT（合并键位）

当需要将两个相邻键合并时：

```python
def compute_merged_rect(rect1, rect2):
    """合并两个 VIEW_RECT，返回新的 VIEW_RECT 字符串"""
    r1 = tuple(int(x) for x in rect1.split(','))
    r2 = tuple(int(x) for x in rect2.split(','))
    
    min_x = min(r1[0], r2[0])
    max_r = max(r1[0] + r1[2], r2[0] + r2[2])
    
    new_w = max_r - min_x
    return f'{min_x},{r1[1]},{new_w},{r1[3]}'
```

## 注意事项

1. **换行符**：BDS 的 INI 文件使用 `\r\n` 换行，写入时保持一致
2. **编码**：文件可能是 GBK 或 UTF-8，读取时用 `errors='replace'` 兜底
3. **不再使用的 KEY**：删除后剩余行之间的空白行可以保留，不影响加载
4. **TIP section**：INI 末尾可能有 `[TIPnn]` section，不要误删或复制
