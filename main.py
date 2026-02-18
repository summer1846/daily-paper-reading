import feedparser
import requests
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ---------------------- 配置区（请修改这里） ----------------------
# 豆包API配置
DOUBAO_API_KEY = "你的豆包API Key"
DOUBAO_API_URL = "https://api.doubao.com/v1/chat/completions"

# 微信推送（Server酱）配置
SERVERCHAN_SENDKEY = "你的Server酱SendKey"
SERVERCHAN_URL = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"

# 邮件配置
SMTP_SERVER = "smtp.qq.com"  # 或 smtp.163.com
SMTP_PORT = 587
SMTP_USER = "你的邮箱地址"
SMTP_PASSWORD = "你的邮箱授权码"
TO_EMAIL = "L120136@ZJU.EDU.CN"

# 监控的顶刊RSS列表
RSS_FEEDS = [
    # 细胞/生命科学IF>10顶刊RSS（全覆盖）
RSS_FEEDS = [
    # 肿瘤免疫核心刊
    "https://jitc.bmj.com/rss/current.xml",          # JITC (IF=10.6)
    "https://cancerdiscovery.aacrjournals.org/rss/current.xml", # Cancer Discovery (IF≈39)
    "https://cancerres.aacrjournals.org/rss/current.xml",       # Cancer Research (IF≈13)
    # 细胞类顶刊
    "https://www.cell.com/rss/current.xml?journal=cell",        # Cell (IF≈66)
    "https://www.cell.com/rss/current.xml?journal=ccell",       # Cancer Cell (IF≈52)
    "https://www.cell.com/rss/current.xml?journal=immunity",    # Immunity (IF≈32)
    "https://www.cell.com/rss/current.xml?journal=devcell",     # Developmental Cell (IF≈12)
    # Nature子刊
    "https://www.nature.com/nature/rss/current.xml",            # Nature (IF≈69)
    "https://www.nature.com/natimmunol/rss/current.xml",        # Nature Immunology (IF≈31)
    "https://www.nature.com/nrc/rss/current.xml",               # Nature Reviews Cancer (IF≈69)
    "https://www.nature.com/ncb/rss/current.xml",               # Nature Cell Biology (IF≈28)
    "https://www.nature.com/nbt/rss/current.xml",               # Nature Biotechnology (IF≈68)
    # Science子刊
    "https://science.sciencemag.org/rss/current.xml",           # Science (IF≈63)
    "https://immunology.sciencemag.org/rss/current.xml",        # Science Immunology (IF≈24)
    # 综合顶刊
    "https://www.cell.com/rss/current.xml?journal=molcell",     # Molecular Cell (IF≈19)
    "https://www.embopress.org/rss/ebo.xml",                    # EMBO Journal (IF≈11)
    "https://www.sciencedirect.com/rss/journal/S0092867423000795", # Cell Metabolism (IF≈29)
    "https://journals.plos.org/plosbiology/rss/current.xml",    # PLOS Biology (IF≈11)
]
]

# 关键词列表
KEYWORDS = [
    "cancer immunology", "CAR-T cell", "T cell", "mitophagy",
    "immune evasion", "novel immune checkpoint", "tumor microenvironment",
    "CD8+ T cell", "immunotherapy", "PD-1", "PD-L1", "CTLA-4"
]
# ----------------------------------------------------------------

def fetch_papers():
    """从RSS抓取论文并过滤关键词"""
    papers = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            # 检查标题或摘要是否包含关键词
            if any(k.lower() in (title + summary).lower() for k in KEYWORDS):
                papers.append({
                    "title": title,
                    "summary": summary,
                    "link": link
                })
    return papers

def analyze_paper(paper):
    """调用豆包AI精读论文"""
    prompt = f"""
你是肿瘤免疫治疗领域专业精读助手，严格按以下格式输出：

【1】论文基本信息
标题：{paper['title']}
链接：{paper['link']}

【2】核心创新点（Novelty）
- 1/2/3条

【3】关键数据与结论（Key Results）
- 最重要3条

【4】图表核心总结（Figure Summary）
- 每张关键图一句话

【5】与我的研究相关性
AQP9、肿瘤免疫、CD8 T细胞浸润、免疫检查点、mitophagy、联合免疫治疗

【6】可借鉴点

论文摘要：
{paper['summary']}
"""
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "doubao-3.5",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    response = requests.post(DOUBAO_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"AI分析失败: {response.text}"

def send_wechat(title, content):
    """通过Server酱推送微信消息"""
    data = {
        "title": title,
        "desp": content
    }
    requests.post(SERVERCHAN_URL, data=data)

def send_email(subject, content):
    """发送邮件"""
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, TO_EMAIL, msg.as_string())

def main():
    print("开始抓取论文...")
    papers = fetch_papers()
    if not papers:
        print("没有找到符合条件的论文。")
        return

    print(f"找到 {len(papers)} 篇论文，开始AI分析...")
    report = f"【每日肿瘤免疫顶刊精读】{datetime.now().strftime('%Y-%m-%d')}\n\n"
    for i, paper in enumerate(papers, 1):
        print(f"分析第 {i}/{len(papers)} 篇: {paper['title']}")
        analysis = analyze_paper(paper)
        report += f"---\n📌 论文 {i}:\n{analysis}\n\n"

    print("生成报告完成，开始推送...")
    send_wechat("每日肿瘤免疫顶刊精读", report)
    send_email("每日肿瘤免疫顶刊精读", report)
    print("推送完成！")

if __name__ == "__main__":
    main()
