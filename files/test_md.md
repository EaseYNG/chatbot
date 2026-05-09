# 🚀 Markdown 测试文本

## 1. 标题层级

### 1.1 三级标题
#### 1.1.1 四级标题
##### 五级标题
###### 六级标题

---

## 2. 文本样式

- **粗体文字**
- *斜体文字*
- ~~删除线~~
- ***粗斜体***
- `行内代码`
- 上标^TM^ 和 下标~H~2~O~

> 这是一段引用文本
> 多行引用
>> 嵌套引用

---

## 3. 列表

### 无序列表
- 苹果
- 香蕉
- 橘子
  - 蜜橘
  - 脐橙

### 有序列表
1. 第一步
2. 第二步
3. 第三步

### 任务列表
- [x] 已完成任务
- [ ] 未完成任务
- [ ] 待办事项

---

## 4. 代码块

### Python 示例
```python
def hello(name):
    """打招呼函数"""
    print(f"Hello, {name}!")
    return True

# 调用函数
hello("Void")
```

### JavaScript 示例
```javascript
const greet = (name) => {
  console.log(`Hello, ${name}!`);
  return {
    message: `Welcome ${name}`,
    timestamp: Date.now()
  };
};
```

### 纯文本代码块
```
$ npm install marked highlight.js
$ npm run dev
```

---

## 5. 表格

| 语言 | 用途 | 难度 |
|------|------|------|
| Python | 数据科学 | ⭐⭐ |
| JavaScript | Web开发 | ⭐⭐⭐ |
| Rust | 系统编程 | ⭐⭐⭐⭐ |
| Go | 后端开发 | ⭐⭐⭐ |

---

## 6. 链接和图片

- [GitHub](https://github.com)
- [Vue.js 官网](https://vuejs.org)

![Vue Logo](https://vuejs.org/images/logo.png)

---

## 7. 数学公式（如果支持）

行内公式：$E = mc^2$

块级公式：

$$
\int_{a}^{b} f(x) \, dx = F(b) - F(a)
$$

---

## 8. 分割线和特殊符号

---

水平线上面

***

星号水平线

---

## 9. 脚注

这是一个带脚注的句子[^1]

[^1]: 这是脚注的内容

---

## 10. 定义列表

Markdown
: 一种轻量级标记语言

HTML
: 超文本标记语言

---

**测试结束！** 🎉 如果以上所有内容都正确渲染，说明你的 Markdown 渲染器工作正常！
