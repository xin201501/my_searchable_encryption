import torch
import torch.nn as nn
import numpy as np  # 新增依赖


# 新增函数实现
def json_to_vector(doc, vocab):
    """
    将JSON文档转换为数值向量
    :param doc: JSON字典对象
    :param vocab: 包含所有特征名称的列表
    :return: numpy数组形式的特征向量
    """
    vector = np.zeros(len(vocab))
    for idx, feature in enumerate(vocab):
        if feature in doc:
            # 基础类型处理（扩展时可添加更复杂的解析逻辑）
            value = doc[feature]
            if isinstance(value, (int, float)):
                vector[idx] = value
            elif isinstance(value, str):
                # 简单哈希归一化处理字符串
                vector[idx] = hash(value) % 10 / 10.0
    return vector.astype(np.float32)


# 后续原有代码保持不变...
class JSONAutoencoder(nn.Module):
    def __init__(self, input_dim=64, hidden_dim=32):
        super().__init__()
        # 编码器
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(), nn.Linear(128, hidden_dim)
        )

        # 解码器
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim),
            nn.Sigmoid(),  # 适用于归一化数据
        )

        # 字段重构头（可选）
        self.user_id_head = nn.Linear(input_dim, 1)  # 数值回归
        self.preference_head = nn.Linear(input_dim, 10)  # 分类输出
        self.active_head = nn.Linear(input_dim, 1)  # 二分类

    def forward(self, x):
        z = self.encoder(x)
        decoded = self.decoder(z)

        # # 多任务输出（可选）
        # user_id_pred = self.user_id_head(decoded)
        # preference_logits = self.preference_head(decoded)
        # active_logits = self.active_head(decoded)

        return decoded


from torch.utils.data import Dataset, DataLoader


# 自定义Dataset类
class JSONDataset(Dataset):
    def __init__(self, data, vocab):
        self.vectors = [json_to_vector(doc, vocab) for doc in data]

    def __len__(self):
        return len(self.vectors)

    def __getitem__(self, idx):
        return torch.tensor(self.vectors[idx])


# 超参数
input_dim = 64  # 向量维度需根据实际数据调整
batch_size = 32

# 初始化模型和优化器
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = JSONAutoencoder(input_dim).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

# 损失函数
mse_loss = nn.MSELoss()
bce_loss = nn.BCEWithLogitsLoss()


# 训练循环
def train(model: torch.nn.Module, dataloader, epochs=20):
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch in dataloader:
            batch = batch.to(device)

            # 前向传播
            # decoded, user_id_pred, preference_logits, active_logits = model(batch)
            decoded = model(batch)

            # 计算损失
            reconstruction_loss = mse_loss(decoded, batch)
            # numeric_loss = mse_loss(
            #     user_id_pred.squeeze(), batch[:, 0]
            # )  # 假设user_id在第一个维度
            # category_loss = bce_loss(
            #     preference_logits,
            #     torch.randint(0, 2, (batch_size, 10)).float().to(device),
            # )  # 示例标签
            # binary_loss = bce_loss(active_logits.squeeze(), batch[:, -1])

            # total = reconstruction_loss + 0.5 * (
            #     numeric_loss + category_loss + binary_loss
            # )
            total = reconstruction_loss

            # 反向传播
            optimizer.zero_grad()
            total.backward()
            optimizer.step()

            total_loss += total.item()

        print(f"Epoch [{epoch + 1}/{epochs}], Loss: {total_loss / len(dataloader):.4f}")
