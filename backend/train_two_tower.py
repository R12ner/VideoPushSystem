import os
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import pickle

# --- 配置 ---
# 脚本在 backend/ 目录下执行, 因此路径是相对于 backend/
DATA_DIR = "./data/ml-latest-small"
MODEL_SAVE_PATH = "./app/services/model_data"
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
METRICS_SAVE_PATH = os.path.join(MODEL_SAVE_PATH, "two_tower_metrics.json")

EMBEDDING_DIM = 64
BATCH_SIZE = 256
EPOCHS = 5
LR = 0.001
SEQ_LEN = 20  # 用户历史行为序列长度

# --- 1. 数据预处理 ---
def load_data():
    print("Loading data...")
    ratings_path = os.path.join(DATA_DIR, 'ratings.csv')
    if not os.path.exists(ratings_path):
        raise FileNotFoundError(f"Ratings file not found at {ratings_path}. Please download the MovieLens ml-latest-small dataset and place it in the '{DATA_DIR}' directory.")

    ratings = pd.read_csv(ratings_path)
    # 隐式反馈：只保留评分 >= 4 的作为正样本
    ratings = ratings[ratings['rating'] >= 4.0]
    
    # ID 映射 (从 1 开始，0 留给 padding)
    user_ids = ratings['userId'].unique()
    item_ids = ratings['movieId'].unique()
    
    user2id = {u: i+1 for i, u in enumerate(user_ids)}
    item2id = {m: i+1 for i, m in enumerate(item_ids)}
    
    ratings['user_idx'] = ratings['userId'].map(user2id)
    ratings['item_idx'] = ratings['movieId'].map(item2id)
    
    # 构建用户历史序列 (按时间排序)
    user_history = ratings.sort_values('timestamp').groupby('user_idx')['item_idx'].apply(list).to_dict()
    
    train_data = []
    # 生成训练样本: (user_id, history_seq, target_item_id)
    for u, items in user_history.items():
        if len(items) < 2: continue
        # 简单切分：最后一次交互为 Target，之前为 History
        target = items[-1]
        history = items[:-1]
        history = history[-SEQ_LEN:] # 截断
        # Padding
        if len(history) < SEQ_LEN:
            history = [0] * (SEQ_LEN - len(history)) + history
        
        train_data.append((u, history, target))
            
    return train_data, len(user2id)+1, len(item2id)+1, item2id

# --- 2. Dataset ---
class RecDataset(Dataset):
    def __init__(self, data):
        self.data = data
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        uid, hist, target = self.data[idx]
        return {
            'user_id': torch.tensor(uid, dtype=torch.long),
            'history': torch.tensor(hist, dtype=torch.long),
            'target_item': torch.tensor(target, dtype=torch.long)
        }

# --- 3. 双塔模型 (User Tower 基于行为序列) ---
class TwoTowerModel(nn.Module):
    def __init__(self, num_users, num_items, embed_dim):
        super().__init__()
        self.item_embedding = nn.Embedding(num_items, embed_dim, padding_idx=0)
        
    def user_tower(self, history):
        # history: [batch, seq_len]
        # [batch, seq_len, dim]
        seq_emb = self.item_embedding(history) 
        # Mean Pooling (忽略 padding 0 的严谨做法略，这里做简单 Mean)
        mask = (history != 0).unsqueeze(-1).float()
        sum_emb = (seq_emb * mask).sum(dim=1)
        count = mask.sum(dim=1).clamp(min=1)
        user_vector = sum_emb / count
        return user_vector # [batch, dim]

    def item_tower(self, item_id):
        return self.item_embedding(item_id) # [batch, dim]
    
    def forward(self, history, target_item):
        user_vec = self.user_tower(history)
        item_vec = self.item_tower(target_item)
        return user_vec, item_vec

# --- 4. 评估指标 ---
def calculate_metrics(user_vecs, target_items, all_item_vecs, k=10):
    # user_vecs: [batch, dim], all_item_vecs: [num_items, dim]
    # 计算点积相似度
    scores = torch.matmul(user_vecs, all_item_vecs.T) # [batch, num_items]
    _, topk_indices = torch.topk(scores, k, dim=1)
    
    hits = 0
    ndcg = 0
    target_items = target_items.cpu().numpy()
    topk_indices = topk_indices.cpu().numpy()
    
    for i, target in enumerate(target_items):
        if target in topk_indices[i]:
            hits += 1
            rank = np.where(topk_indices[i] == target)[0][0]
            ndcg += 1.0 / np.log2(rank + 2)
            
    return hits / len(target_items), ndcg / len(target_items)

# --- 5. 训练主流程 ---
if __name__ == "__main__":
    
    try:
        train_data, n_users, n_items, item2id = load_data()
    except FileNotFoundError as e:
        print(e)
        exit()

    train_set, val_set = train_test_split(train_data, test_size=0.1, random_state=42)
    
    train_loader = DataLoader(RecDataset(train_set), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(RecDataset(val_set), batch_size=BATCH_SIZE)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TwoTowerModel(n_users, n_items, EMBEDDING_DIM).to(device)
    optimizer = optim.Adam(model.parameters(), lr=LR)
    metrics_history = []
    
    print("Start Training...")
    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        for batch in tqdm(train_loader):
            hist = batch['history'].to(device)
            target = batch['target_item'].to(device)
            
            user_vec, item_vec = model(hist, target)
            
            logits = torch.matmul(user_vec, item_vec.T) 
            labels = torch.arange(logits.size(0)).to(device)
            
            loss = nn.CrossEntropyLoss()(logits, labels)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        avg_loss = total_loss / len(train_loader)
        print(f"Epoch {epoch+1}, Loss: {avg_loss:.4f}")
        
        model.eval()
        all_item_ids = torch.arange(n_items).to(device)
        with torch.no_grad():
            all_item_vecs = model.item_embedding(all_item_ids)
            
            batch = next(iter(val_loader))
            hist = batch['history'].to(device)
            target = batch['target_item'].to(device)
            u_vec = model.user_tower(hist)
            recall, ndcg = calculate_metrics(u_vec, target, all_item_vecs, k=10)
            print(f"Val Recall@10: {recall:.4f}, NDCG@10: {ndcg:.4f}")

        metrics_history.append({
            "epoch": epoch + 1,
            "loss": round(float(avg_loss), 6),
            "recall_at_10": round(float(recall), 6),
            "ndcg_at_10": round(float(ndcg), 6)
        })

    # --- 6. 导出模型与数据 ---
    print("Exporting...")
    all_item_vecs = model.item_embedding(torch.arange(n_items).to(device)).cpu().detach().numpy()
    id2item = {v: k for k, v in item2id.items()} 
    
    export_data = {
        "item_embeddings": all_item_vecs, # numpy array [n_items, dim]
        "item2id_map": item2id,           # dict: real_id -> model_idx
        "id2item_map": id2item,           # dict: model_idx -> real_id
        "embedding_dim": EMBEDDING_DIM
    }
    
    with open(os.path.join(MODEL_SAVE_PATH, "recall_data.pkl"), "wb") as f:
        pickle.dump(export_data, f)

    metrics_payload = {
        "model_name": "Two-Tower Recall",
        "dataset": "MovieLens ml-latest-small",
        "trained_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "embedding_dim": EMBEDDING_DIM,
            "batch_size": BATCH_SIZE,
            "epochs": EPOCHS,
            "learning_rate": LR,
            "sequence_length": SEQ_LEN,
            "num_users": int(n_users - 1),
            "num_items": int(n_items - 1)
        },
        "history": metrics_history
    }

    with open(METRICS_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, ensure_ascii=False, indent=2)
        
    torch.save(model.state_dict(), os.path.join(MODEL_SAVE_PATH, "two_tower_model.pth"))
    print(f"Model and data exported to {MODEL_SAVE_PATH}")
    print("Done.")
