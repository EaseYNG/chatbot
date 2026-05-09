# FastAPI 示例代码

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# 创建应用实例
app = FastAPI(title="My API", version="1.0.0")

# 数据模型
class Item(BaseModel):
    name: str
    price: float
    description: Optional[str] = None

# 模拟数据库
items_db = {}

# 根路由
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

# 创建物品（POST）
@app.post("/items/")
def create_item(item: Item):
    item_id = len(items_db) + 1
    items_db[item_id] = item
    return {"item_id": item_id, **item.model_dump()}

# 获取单个物品（GET）
@app.get("/items/{item_id}")
def read_item(item_id: int):
    item = items_db.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, **item.model_dump()}

# 获取所有物品（GET）
@app.get("/items/")
def read_all_items():
    return items_db

# 运行方式（在终端执行）：
# uvicorn 文件名:app --reload
# 例如：uvicorn fastapi_demo:app --reload
```
