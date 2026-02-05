import requests
import json
import os
import time
from datetime import datetime, timedelta

class WeChatArticleDownloader:
    def __init__(self, api_key="d6b88e7f639a4b2caf3ccd8f72ba251f"):
        """
        初始化下载器
        :param api_key: API 访问密钥
        """
        self.api_key = api_key
        self.base_url = "https://down.mptext.top/api/public/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "X-Auth-Key": api_key  # 使用官方推荐的认证头
        })
    
    def _request(self, endpoint, method="GET", data=None):
        """
        发送 API 请求
        :param endpoint: API 端点
        :param method: 请求方法
        :param data: 请求参数
        :return: API 响应（JSON 格式）
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            # 不需要添加 api_key 作为查询参数，已在 headers 中
            
            if method == "GET":
                response = self.session.get(url, params=data, timeout=30)
            else:
                response = self.session.post(url, json=data, timeout=30)
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None
    
    def search_accounts(self, keyword, page=1, page_size=20):
        """
        根据关键字搜索公众号
        :param keyword: 搜索关键字
        :param page: 页码
        :param page_size: 每页数量
        :return: 公众号列表（只包含完全匹配的）
        """
        params = {
            "keyword": keyword,
            "page": page,
            "page_size": page_size
        }
        response = self._request("account", data=params)
        # 检查响应格式，数据在 list 字段中，并过滤出完全匹配的公众号
        if response and "list" in response:
            # 只保留 nickname 和 keyword 完全匹配的公众号
            matched_accounts = [
                account for account in response["list"] 
                if account.get("nickname") == keyword
            ]
            return {"data": matched_accounts}  # 转换为统一格式
        return response
    
    def get_articles(self, account_id, page=1, page_size=10):
        """
        获取指定公众号的文章列表
        :param account_id: 公众号 ID（fakeid）
        :param page: 页码
        :param page_size: 每页数量（默认前 10 篇）
        :return: 文章列表
        """
        params = {
            "fakeid": account_id,  # 使用 fakeid 作为参数名
            "page": page,
            "page_size": page_size
        }
        
        response = self._request("article", data=params)
        
        # 检查响应格式，数据可能在 list 或 articles 字段中
        if response:
            if "list" in response:
                return {"data": response["list"]}  # 转换为统一格式
            elif "articles" in response:
                return {"data": response["articles"]}  # 转换为统一格式
        return response
    
    def download_article(self, article_url, article_title=None, save_dir=None, account_name=None, publish_time=None):
        """
        下载文章并保存为 markdown 格式
        :param article_url: 文章 URL
        :param article_title: 文章原始标题
        :param save_dir: 保存目录（默认以当天日期命名）
        :param account_name: 公众号名称
        :param publish_time: 文章发布时间（datetime对象）
        :return: 是否下载成功
        """
        # 使用当天日期作为默认目录名
        if save_dir is None:
            today = datetime.now().strftime("%Y-%m-%d")
            save_dir = f"./{today}"
        
        # 检查是否是当天的文件夹
        today = datetime.now().strftime("%Y-%m-%d")
        if save_dir == f"./{today}":
            # 每次下载都在当天日期文件夹内创建小时子文件夹
            time_suffix = datetime.now().strftime("%H时")
            save_dir = f"./{today}/{time_suffix}"
        
        # 创建保存目录
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 构建下载参数
        params = {
            "url": article_url if article_url.startswith("http") else f"https://mp.weixin.qq.com/s/{article_url}",
            "format": "markdown"
        }
        
        # 发送下载请求
        url = f"{self.base_url}/download"
        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            # 获取文章标题作为文件名
            content = response.text
            
            # 使用传入的原始标题或从内容中提取标题
            title = article_title or "untitled"
            if title == "untitled":
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('# '):
                        title = line[2:].strip()
                        break
            
            # 在标题前面加上公众号名称，用【】隔开
            if account_name:
                title = f"【{account_name}】{title}"
            
            
            
            # 移除文件名中的非法字符
            title = "".join(c for c in title if c not in '\\/:*?"<>|')
            if title == "untitled":
                title = f"article_{article_url.split('/')[-1]}"
            
            # 生成文件路径
            filename = f"{title}.md"
            filepath = os.path.join(save_dir, filename)
            
            # 检查文章是否已经下载过（包括当天目录下的所有子文件夹）
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_dir = f"./{today_str}"
            article_exists = False
            
            # 检查当前文件路径是否存在
            if os.path.exists(filepath):
                article_exists = True
            # 检查当天目录下的所有子文件夹
            elif os.path.exists(today_dir):
                for root, dirs, files in os.walk(today_dir):
                    for file in files:
                        if file == filename:
                            article_exists = True
                            break
                    if article_exists:
                        break
            
            if article_exists:
                print(f"文章已存在，跳过下载: {filename}")
                return False
            
            # 在文章内容最前方添加发布时间
            if publish_time:
                time_str = publish_time.strftime("%Y-%m-%d %H:%M")
                content = f"> 发布时间: {time_str}\n\n{content}"
            
            # 删除以" #js"开头的行
            lines = content.split('\n')
            filtered_lines = [line for line in lines if not line.strip().startswith('#js')]
            content = '\n'.join(filtered_lines)
            
            # 保存文件
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"文章已下载: {filepath}")
            return True
        except requests.RequestException as e:
            print(f"下载文章失败: {e}")
            return False
    
    def batch_download_articles(self, account_id, account_name, save_dir=None, days_limit=0):
        """
        批量下载指定公众号的文章
        :param account_id: 公众号 ID（fakeid）
        :param account_name: 公众号名称
        :param save_dir: 保存目录
        :param days_limit: 下载前几天的文章，0表示只下载今天的
        :return: 成功下载的文章数量
        """

        
        # 获取文章列表
        articles_response = self.get_articles(account_id, page_size=100)  # 增加 page_size 以获取更多文章
        if not articles_response or "data" not in articles_response:
            print("获取文章列表失败")
            return 0
        
        articles = articles_response["data"]
        print(f"找到 {len(articles)} 篇文章")
        
        # 过滤文章
        filtered_articles = []
        if days_limit >= 0:
            today = datetime.now()
            # 转换为只包含日期的datetime对象，忽略时间部分
            today_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = today_date
            if days_limit > 0:
                start_date = today_date - timedelta(days=days_limit)
            start_date_str = start_date.strftime("%Y-%m-%d")
            today_str = today_date.strftime("%Y-%m-%d")
            
            if days_limit == 0:
                print(f"\n过滤今天 ({today_str}) 发布的文章...")
            else:
                print(f"\n过滤 {start_date_str} 到 {today_str} 发布的文章...")
            
            for article in articles:
                # 获取文章的发布时间
                update_time = article.get("update_time") or article.get("create_time")
                if update_time:
                    # 将时间戳转换为日期
                    article_date = datetime.fromtimestamp(update_time)
                    # 转换为只包含日期的datetime对象，忽略时间部分
                    article_date_only = article_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    article_date_str = article_date_only.strftime("%Y-%m-%d")
                    # 检查文章是否在指定的日期范围内
                    if article_date_only >= start_date:
                        filtered_articles.append(article)
            
            if days_limit == 0:
                print(f"找到 {len(filtered_articles)} 篇今天发布的文章")
            else:
                print(f"找到 {len(filtered_articles)} 篇近 {days_limit} 天发布的文章")
        else:
            filtered_articles = articles
        
        # 逐个下载
        success_count = 0
        for article in filtered_articles:
            article_url = article.get("url") or article.get("link") or article.get("content_url")
            article_title = article.get("title")  # 获取文章原始标题
            if article_url:
                    # 获取文章发布日期，用于创建对应文件夹
                    update_time = article.get("update_time") or article.get("create_time")
                    article_date_dir = save_dir
                    publish_time = None
                    if update_time:
                        # 根据文章发布日期创建文件夹
                        article_date = datetime.fromtimestamp(update_time).strftime("%Y-%m-%d")
                        article_date_dir = f"./{article_date}"
                        # 转换为datetime对象，用于传递给download_article
                        publish_time = datetime.fromtimestamp(update_time)
                    
                    if self.download_article(article_url, article_title, article_date_dir, account_name, publish_time):
                        success_count += 1
                    # 避免请求过快
                    time.sleep(1)
        
        print(f"批量下载完成，成功 {success_count} 篇")
        return success_count

if __name__ == "__main__":
    print("===== 公众号文章下载器 =====")
    print("\n核心功能:")
    print("1. 从配置文件读取公众号关键词")
    print("2. 自动搜索并处理所有公众号")
    print("3. 下载公众号当天发布的所有文章")
    print("4. 保存为 markdown 格式，保留原始文章标题")
    print("\n注意:")
    print("- 配置文件: config.json")
    print("- 保存目录以当天日期命名")
    print("- 文章格式为 markdown")
    print("- 已内置 API 密钥")
    print("- 只输出和关键字完全匹配的公众号")
    print("\n开始使用:")
    
    # 读取配置文件
    config_file = "config.json"
    if not os.path.exists(config_file):
        print(f"错误: 配置文件 {config_file} 不存在")
        print("请创建配置文件，示例格式:")
        print('''
{
  "keywords": [
    "财联社",
    "财联社早知道"
  ],
  "days_limit": 0,  # 下载前几天的文章，0表示只下载今天的，1表示下载今天和昨天的，以此类推
  "page_size": 100
}
        ''')
        exit(1)
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        api_key = config.get("api_key", "d6b88e7f639a4b2caf3ccd8f72ba251f")
        keywords = config.get("keywords", [])
        days_limit = config.get("days_limit", 0)  # 新增配置项，默认值为0，表示只下载当天的文章
        
        if not keywords:
            print("错误: 配置文件中未设置 keywords")
            exit(1)
        
        print(f"\n从配置文件读取到 {len(keywords)} 个公众号关键词:")
        for keyword in keywords:
            print(f"- {keyword}")
        
        if days_limit == 0:
            print("\n设置: 只下载今天发布的文章")
        else:
            print(f"\n设置: 下载前 {days_limit} 天发布的文章")
        
    except json.JSONDecodeError as e:
        print(f"错误: 配置文件格式错误 - {e}")
        exit(1)
    except Exception as e:
        print(f"错误: 读取配置文件失败 - {e}")
        exit(1)
    
    # 初始化下载器
    downloader = WeChatArticleDownloader(api_key=api_key)
    
    # 遍历所有关键词
    total_success = 0
    for keyword in keywords:
        print(f"\n=== 处理关键词: {keyword} ===")
        
        # 根据关键字搜索公众号
        accounts = downloader.search_accounts(keyword)
        
        if accounts and "data" in accounts and len(accounts["data"]) > 0:
            print(f"找到 {len(accounts['data'])} 个完全匹配的公众号:")
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
