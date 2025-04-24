from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import itertools

left_words = ["老年人", "老人", "中老年"]
right_words = ["书", "书籍", "读物"]
keywords = [f"{l} {r}" for l, r in itertools.product(left_words, right_words)]

def crawl_titles(keywords, pages=5):
    options = Options()
    options.add_argument(r"user-data-dir=C:\Codes\python scripts\books\selenium_cache_jd")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.jd.com/")
    time.sleep(3)

    results = []

    for keyword in keywords:
        print(f"\n🔍 当前关键词：{keyword}")
        for page in range(1, pages + 1):
            url = (
                f"https://search.jd.com/Search?keyword={keyword}&stock=1&psort=3&click=1&page={page * 2 - 1}"
            )
            print(f"📄 第 {page} 页：{url}")
            driver.get(url)
            time.sleep(2)

            for _ in range(10):
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(0.5)

            items = driver.find_elements(By.CSS_SELECTOR, ".p-name em")

            if not items:
                print(f"⚠️ 第 {page} 页没有找到书名元素，很可能是验证页面或页面加载失败")
                print("⏸ 请你手动查看浏览器页面是否为验证页（如滑动验证），完成后按回车继续尝试抓取...")

                input("👉 验证完成后按回车重试当前页：")

                # 重试当前页
                driver.get(url)
                time.sleep(2)
                for _ in range(10):
                    driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(0.5)

                items = driver.find_elements(By.CSS_SELECTOR, ".p-name em")
                if not items:
                    print("❌ 重试后仍未抓到书名，跳过该页。")
                    continue

            for idx, el in enumerate(items):
                try:
                    title = el.text.strip()
                    results.append({
                        "关键词": keyword,
                        "页码": page,
                        "序号": idx + 1,
                        "书名": title
                    })
                except Exception:
                    continue

    driver.quit()
    return pd.DataFrame(results)

def compute_ranking(df, decay=0.85):
    df["score"] = 100 * (decay ** (df["页码"] - 1)) * (1 - (df["序号"] - 1) / 30)
    df.to_csv("老年图书_双词组合分析.csv", index=False, encoding="utf-8-sig")

    grouped = df.groupby("书名").agg(
        总得分=("score", "sum"),
        出现次数=("score", "count"),
        覆盖关键词=("关键词", lambda x: ", ".join(sorted(set(x)))),
        最早页码=("页码", "min"),
        最早序号=("序号", "min"),
    ).reset_index()

    grouped_sorted = grouped.sort_values(by="总得分", ascending=False)

    with open("老年图书_推荐排序_0.85_decay_简洁版.txt", "w", encoding="utf-8") as f:
        for i, row in enumerate(grouped_sorted.itertuples(index=False), 1):
            f.write(f"{i}.《{row.书名}》，综合得分：{row.总得分:.2f}\n")

    grouped_sorted.to_csv("老年图书_推荐排序_0.85_decay.csv", index=False, encoding="utf-8-sig")

    print("\n✅ 排序已完成！输出文件：")
    print("📄 老年图书_双词组合分析.csv")
    print("📄 老年图书_推荐排序_0.85_decay.csv")
    print("📄 老年图书_推荐排序_0.85_decay_简洁版.txt")

if __name__ == "__main__":
    raw_df = crawl_titles(keywords, pages=5)
    compute_ranking(raw_df, decay=0.85)
