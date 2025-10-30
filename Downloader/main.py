import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re
import sys
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def sanitize_filename(name: str, max_length: int = 200) -> str:
    # Windows 금지 문자 제거
    name = re.sub(r'[<>:"/\\|?*\n\r\t]+', "_", name).strip()
    if len(name) > max_length:
        name = name[:max_length].rstrip()
    return name or "article"

def fetch(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.text

def extract_title_and_body(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # 제목 추출: og:title 우선, 없으면 <title>
    title_tag = soup.find("meta", property="og:title")
    if title_tag and title_tag.get("content"):
        title = title_tag["content"].strip()
    else:
        title = (soup.title.string if soup.title and soup.title.string else "").strip()

    # 본문 추출을 위한 가능한 선택자들
    selectors = [
        {"id": "articleBodyContents"},
        {"id": "dic_area"},
        {"id": "newsEndContents"},
        {"id": "newsEndContentsWrap"},
        {"class_": "newsct_article"},
        {"class_": "news_end"},
        {"class_": "article_body"},
        {"tag": "article"},
        {"id": "articeBody"},  # 오타 변형 대비
    ]

    body_text = None
    for sel in selectors:
        node = None
        if "id" in sel:
            node = soup.find(id=sel["id"])
        elif "class_" in sel:
            node = soup.find("div", class_=sel["class_"])
        elif "tag" in sel:
            node = soup.find(sel["tag"])

        if node:
            # 광고/스크립트/불필요 요소 제거
            for bad in node(["script", "style", "iframe", "aside", "ins"]):
                bad.decompose()
            text = node.get_text(separator="\n").strip()
            if text:
                body_text = text
                break

    # 보조 전략: article 태그 없을 때 큰 텍스트 블록 선택
    if not body_text:
        paragraphs = soup.find_all(["p", "div"])
        # 길이가 일정 이상인 첫 텍스트 블록 사용
        for p in paragraphs:
            txt = p.get_text(separator="\n").strip()
            if len(txt) > 200:
                body_text = txt
                break

    if body_text:
        # 불필요한 연속 공백, 광고 문구 제거(간단 처리)
        body_text = re.sub(r"\n{2,}", "\n\n", body_text)
        body_text = body_text.strip()

    return title, body_text

def save_article(title: str, body: str, date_str: str) -> Path:
    """
    기사를 파일로 저장
    
    Args:
        title: 기사 제목
        body: 기사 본문
        date_str: 날짜 문자열 (yyyymmdd 형식)
    
    Returns:
        Path: 저장된 파일 경로
    """
    # 현재 폴더 경로
    current_folder = Path(__file__).resolve().parent
    
    # data 폴더 경로
    data_folder = current_folder / "data"
    
    # data 폴더가 없으면 생성
    data_folder.mkdir(parents=True, exist_ok=True)
    
    # data/date_str 폴더 경로
    date_folder = data_folder / date_str
    
    # date_str 폴더가 없으면 생성
    date_folder.mkdir(parents=True, exist_ok=True)
    
    # 파일명 생성 및 저장
    filename = sanitize_filename(title) + ".txt"
    file_path = date_folder / filename
    file_path.write_text(body, encoding="utf-8")
    
    return file_path

def get_all_article_urls_with_selenium(section_num: str, group_num: str, date_str: str) -> list:
    """
    네이버 뉴스 페이지에서 모든 기사 URL을 수집
    
    Args:
        section_num: 섹션 번호 (예: "101")
        group_num: 그룹 번호 (예: "259")
        date_str: 날짜 문자열 (예: "20251029")
    
    Returns:
        list: 기사 URL 리스트
    """
    url = f"https://news.naver.com/breakingnews/section/{section_num}/{group_num}?date={date_str}"
    
    # Chrome 드라이버 옵션 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 브라우저 창을 띄우지 않음
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=options)
    article_urls = []
    
    try:
        # 페이지 로드
        driver.get(url)
        time.sleep(2)  # 페이지 로딩 대기
        
        # 더보기 버튼을 최대 50번까지만 클릭
        max_clicks = 50
        click_count = 0
        
        while click_count < max_clicks:
            try:
                # 더보기 버튼 찾기
                more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.section_more_inner"))
                )
                
                # 버튼이 화면에 보이도록 스크롤
                driver.execute_script("arguments[0].scrollIntoView(true);", more_button)
                time.sleep(0.5)
                
                # 더보기 버튼 클릭
                more_button.click()
                click_count += 1
                print(f"더보기 버튼 클릭 ({click_count}/{max_clicks})")
                time.sleep(1.5)  # 콘텐츠 로딩 대기
                
            except (TimeoutException, NoSuchElementException):
                # 더보기 버튼이 없으면 모든 기사가 로드된 것
                print(f"모든 기사 로드 완료 (총 {click_count}번 클릭)")
                break
        
        if click_count >= max_clicks:
            print(f"최대 클릭 횟수({max_clicks})에 도달했습니다.")
        
        # 기사 URL 수집
        # 1) 'section_latest_article' div 선택
        article_container = driver.find_element(By.CSS_SELECTOR, "div.section_latest_article")
        
        # 2) 해당 div 안의 모든 기사 링크 찾기
        article_links = article_container.find_elements(By.CSS_SELECTOR, "a.sa_text_title")
        
        # href 속성에서 URL 추출
        for link in article_links:
            href = link.get_attribute("href")
            if href and href.startswith("https://n.news.naver.com/mnews/article/"):
                article_urls.append(href)
        
        print(f"총 {len(article_urls)}개의 기사 URL 수집 완료")
        
    except Exception as e:
        print(f"Error occurred: {e}")
    
    finally:
        # 드라이버 종료
        driver.quit()
    
    return article_urls

def download_article(url: str, date_str: str) -> bool:
    """
    URL에 있는 기사를 다운로드해서 파일로 저장
    
    Args:
        url: 기사 URL
        date_str: 날짜 문자열 (yyyymmdd 형식)
    
    Returns:
        bool: 성공 시 True, 실패 시 False
    """
    try:
        # 1. fetch()를 사용하여 HTML 가져오기
        html = fetch(url)
        
        # 2. extract_title_and_body()를 사용하여 제목과 본문 추출
        title, body = extract_title_and_body(html)
        
        # 제목 검증
        if not title:
            print(f"Failed to extract title from {url}")
            return False
        
        # 본문 검증
        if not body:
            print(f"Failed to extract body from {url}")
            return False
        
        # 3. save_article()로 파일 저장
        saved_path = save_article(title, body, date_str)
        print(f"Saved: {saved_path}")
        return True
        
    except Exception as e:
        print(f"Error downloading article from {url}: {e}")
        return False

def get_all_articles_by_date(section_num: str, date_str: str) -> list:
    """
    주어진 날짜와 섹션에 대해 8개 그룹의 모든 기사 URL을 수집
    
    Args:
        section_num: 섹션 번호 (예: "101")
        date_str: 날짜 문자열 (yyyymmdd 형식, 예: "20251029")
    
    Returns:
        list: 모든 그룹의 기사 URL을 합친 리스트
    """
    group_nums = [259, 258, 261, 771, 260, 262, 310, 263]
    all_article_urls = []
    
    for group_num in group_nums:
        print(f"\n=== 그룹 {group_num} 처리 중 ===")
        try:
            # 각 그룹별로 기사 URL 수집
            urls = get_all_article_urls_with_selenium(section_num, str(group_num), date_str)
            all_article_urls.extend(urls)
            print(f"그룹 {group_num}: {len(urls)}개 기사 수집")
        except Exception as e:
            print(f"그룹 {group_num} 처리 중 오류 발생: {e}")
            continue
    
    # 중복 제거 (같은 기사가 여러 그룹에 있을 수 있음)
    unique_urls = list(set(all_article_urls))
    print(f"\n총 {len(all_article_urls)}개 수집, 중복 제거 후 {len(unique_urls)}개")
    
    return unique_urls

def get_articles_by_date_range(section_num: str, group_num: str, start_date: str, end_date: str) -> list:
    """
    날짜 기간 동안의 모든 기사 URL을 수집
    
    Args:
        section_num: 섹션 번호 (예: "101")
        group_num: 그룹 번호 (예: "259")
        start_date: 시작 날짜 (yyyymmdd 형식, 예: "20251020")
        end_date: 종료 날짜 (yyyymmdd 형식, 예: "20251029")
    
    Returns:
        list: 기간 내 모든 기사 URL을 합친 리스트
    """
    # 문자열을 datetime 객체로 변환
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    
    # 날짜 유효성 검사
    if start > end:
        print("Error: 시작 날짜가 종료 날짜보다 늦습니다.")
        return []
    
    all_article_urls = []
    current_date = start
    
    # 시작 날짜부터 종료 날짜까지 반복
    while current_date <= end:
        date_str = current_date.strftime("%Y%m%d")
        print(f"\n{'='*50}")
        print(f"날짜: {date_str} 처리 중")
        print(f"{'='*50}")
        
        try:
            # 해당 날짜의 기사 URL 수집
            urls = get_all_article_urls_with_selenium(section_num, group_num, date_str)
            all_article_urls.extend(urls)
            print(f"{date_str}: {len(urls)}개 기사 수집")
        except Exception as e:
            print(f"{date_str} 처리 중 오류 발생: {e}")
        
        # 다음 날로 이동
        current_date += timedelta(days=1)
        
        # 서버 부하 방지를 위한 대기
        time.sleep(2)
    
    # 중복 제거
    unique_urls = list(set(all_article_urls))
    
    print(f"\n{'='*50}")
    print(f"전체 기간 수집 완료")
    print(f"총 {len(all_article_urls)}개 수집, 중복 제거 후 {len(unique_urls)}개")
    print(f"{'='*50}")
    
    return unique_urls

def download_articles_by_date_range(start_date: str, end_date: str, section_num: str, group_num: str) -> dict:
    """
    날짜 기간 동안의 모든 기사를 날짜별로 다운로드
    
    Args:
        start_date: 시작 날짜 (yyyymmdd 형식, 예: "20251020")
        end_date: 종료 날짜 (yyyymmdd 형식, 예: "20251029")
        section_num: 섹션 번호 (예: "101")
        group_num: 그룹 번호 (예: "259")
    
    Returns:
        dict: 다운로드 결과 통계 (성공 개수, 실패 개수, 총 개수)
    """
    print(f"\n{'='*60}")
    print(f"기간: {start_date} ~ {end_date}")
    print(f"섹션: {section_num}, 그룹: {group_num}")
    print(f"{'='*60}\n")
    
    # 문자열을 datetime 객체로 변환
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    
    # 날짜 유효성 검사
    if start > end:
        print("Error: 시작 날짜가 종료 날짜보다 늦습니다.")
        return {"success": 0, "fail": 0, "total": 0}
    
    total_success = 0
    total_fail = 0
    total_articles = 0
    
    current_date = start
    
    # 시작 날짜부터 종료 날짜까지 반복
    while current_date <= end:
        date_str = current_date.strftime("%Y%m%d")
        
        print(f"\n{'='*60}")
        print(f"날짜: {date_str} 처리 시작")
        print(f"{'='*60}")
        
        try:
            # 1. 해당 날짜의 기사 URL 수집
            article_urls = get_all_article_urls_with_selenium(section_num, group_num, date_str)
            
            if not article_urls:
                print(f"{date_str}: 수집된 기사가 없습니다.")
                current_date += timedelta(days=1)
                continue
            print(f"\n{date_str}: {len(article_urls)}개 기사 다운로드 시작")
            
            # 2. 해당 날짜의 기사들을 다운로드 (해당 날짜 폴더에 저장)
            success_count = 0
            fail_count = 0
            
            for i, url in enumerate(article_urls, 1):
                print(f"  [{i}/{len(article_urls)}] 다운로드 중...")
                if download_article(url, date_str):  # 해당 날짜 폴더에 저장
                    success_count += 1
                else:
                    fail_count += 1
                time.sleep(0.5)  # 서버 부하 방지
            
            # 날짜별 통계
            total_success += success_count
            total_fail += fail_count
            total_articles += len(article_urls)
            
            print(f"\n{date_str} 완료:")
            print(f"  - 성공: {success_count}개")
            print(f"  - 실패: {fail_count}개")
            print(f"  - 총: {len(article_urls)}개")
            
        except Exception as e:
            print(f"{date_str} 처리 중 오류 발생: {e}")
        
        # 다음 날로 이동
        current_date += timedelta(days=1)
        
        # 날짜 간 대기 (서버 부하 방지)
        time.sleep(2)
    
    # 전체 결과 출력
    print(f"\n{'='*60}")
    print(f"전체 기간 다운로드 완료")
    print(f"{'='*60}")
    print(f"성공: {total_success}개")
    print(f"실패: {total_fail}개")
    print(f"총: {total_articles}개")
    print(f"{'='*60}\n")
    
    return {
        "success": total_success,
        "fail": total_fail,
        "total": total_articles
    }

def main():
    # 기간 설정
    start_date = "20251020"
    end_date = "20251024"
    section_num = "101"  # 경제
    group_num = "259"    # 금융
    
    # 기간 내 모든 기사 다운로드 (기존 함수들 활용)
    result = download_articles_by_date_range(start_date, end_date, section_num, group_num)
    
    print(f"\n최종 결과:")
    print(f"  - 성공: {result['success']}개")
    print(f"  - 실패: {result['fail']}개")
    print(f"  - 총: {result['total']}개")

if __name__ == "__main__":    
    main()
