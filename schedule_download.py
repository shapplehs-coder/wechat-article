import schedule
import time
import os
import sys

# 添加当前目录到系统路径，以便导入 wechat_article_downloader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from wechat_article_downloader import WeChatArticleDownloader
import json
from datetime import datetime

def download_articles():
    """
    执行文章下载任务
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行文章下载任务...")
    
    # 读取配置文件
    config_file = "config.json"
    if not os.path.exists(config_file):
        print(f"错误: 配置文件 {config_file} 不存在")
        return
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        api_key = config.get("api_key", "d6b88e7f639a4b2caf3ccd8f72ba251f")
        keywords = config.get("keywords", [])
        days_limit = config.get("days_limit", 0)
        
        if not keywords:
            print("错误: 配置文件中未设置 keywords")
            return
        
        print(f"从配置文件读取到 {len(keywords)} 个公众号关键词")
        print(f"下载前 {days_limit} 天发布的文章")
        
        # 初始化下载器
        downloader = WeChatArticleDownloader(api_key=api_key)
        
        # 遍历所有关键词
        total_success = 0
        for keyword in keywords:
            print(f"\n=== 处理关键词: {keyword} ===")
            
            # 根据关键字搜索公众号
            accounts = downloader.search_accounts(keyword)
            
            if accounts and "data" in accounts and len(accounts["data"]) > 0:
                print(f"找到 {len(accounts['data'])} 个完全匹配的公众号")
                for i, account in enumerate(accounts["data"]):
                    print(f"{i+1}. ID: {account.get('fakeid')}, 名称: {account.get('nickname')}")
                
                # 处理所有找到的公众号
                for account in accounts["data"]:
                    account_id = account.get("fakeid")
                    account_name = account.get("nickname")
                    
                    if account_id and account_name:
                        print(f"\n处理公众号: {account_name} (ID: {account_id})")
                        print(f"获取公众号 '{account_name}' 的文章列表...")
                        
                        # 批量下载文章
                        print(f"开始下载公众号 '{account_name}' 的文章...")
                        if days_limit == 0:
                            print("只下载今天发布的文章...")
                        else:
                            print(f"下载前 {days_limit} 天发布的文章...")
                        success_count = downloader.batch_download_articles(account_id, account_name, days_limit=days_limit)
                        total_success += success_count
                    else:
                        print(f"\n跳过无效公众号: {account}")
            else:
                print(f"未找到与 '{keyword}' 完全匹配的公众号")
        
        print(f"\n所有公众号处理完成!")
        print(f"总共成功下载 {total_success} 篇文章")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 文章下载任务执行完成\n")
        
    except json.JSONDecodeError as e:
        print(f"错误: 配置文件格式错误 - {e}")
    except Exception as e:
        print(f"错误: 执行下载任务失败 - {e}")

# 设置定时任务
def setup_schedule():
    """
    设置定时任务
    """
    # 读取配置文件中的定时任务时间
    config_file = "config.json"
    schedule_times = ["08:00", "22:00"]  # 默认时间
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            schedule_times = config.get("schedule_times", ["08:00", "22:00"])
        except Exception as e:
            print(f"读取定时任务配置失败: {e}")
    
    # 设置定时任务
    for time_str in schedule_times:
        schedule.every().day.at(time_str).do(download_articles)
    
    # 打印定时任务信息
    print("定时任务已设置:")
    for i, time_str in enumerate(schedule_times, 1):
        print(f"{i}. 每天 {time_str} 执行文章下载")
    print("\n按 Ctrl+C 退出定时任务\n")

if __name__ == "__main__":
    # 设置定时任务
    setup_schedule()
    
    # 运行无限循环，检查和执行定时任务
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次
