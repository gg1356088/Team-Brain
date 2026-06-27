## GitHub 仓库上传记录

**仓库地址：** git@github.com:gg1356088/Team-Brain.git

**上传内容：**
1. skill_distribution/ — 含 skills-obsidian、team-frameworks、loop-dispatch、README.md
2. 发票自动化工作流/ — 含所有脚本和文档
3. 删除了 00从这里开始.md（系统引导文件，不上仓库）

**上传方式：**
- 首次 clone：git clone https://gg1356088:TOKEN@github.com/gg1356088/Team-Brain.git
- 首次 push：git push origin main（HTTPS + token 内嵌 URL）
- SSH key：已生成 ~/.ssh/id_ed25519，公钥已添加到 GitHub settings/keys
- 清理脏文件：git rm --cached 移除 .DS_Store、__pycache__、download.html 等
- 最终验证：全新 clone 确认远程仓库干净

**遇到的问题：**
- HTTPS token 认证 git push 不稳定（curl API 能通但 git 协议 401）
- SSH 连接被 GitHub 限流（Connection closed by 198.18.0.21 port 22）
- 最终用 HTTPS + token 内嵌 URL 方式 push 成功
