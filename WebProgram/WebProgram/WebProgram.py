import reflex as rx
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, TypedDict
import csv

class WordCount(TypedDict):
    word: str
    count: str

class DateCard(TypedDict):
    date: str
    words: List[WordCount]

class SummaryItem(TypedDict):
    category: str
    summary: str

class State(rx.State):
    # 현재 선택된 메뉴 상태 관리
    current_page: str = "Dashboard"
    selected_date: str = ""

    # KPI 데이터 리스트: [{"title": "20251020", "word": "금융", "count": "2509"}, ...]
    kpi_data: List[Dict[str, str]] = []
    
    # 카드 데이터 리스트: [{"date": "20251020", "words": [{"word": "금융", "count": "2509"}, ...]}, ...]
    card_data: List[DateCard] = []
    
    # 히트맵 데이터: [{"date": "20251020", "word": "금융", "count": 2509}, ...]
    heatmap_data: List[Dict[str, Any]] = []
    
    # 라인 차트 데이터: [{"date": "20251020", "금융": 2509, "대출": 1253, ...}, ...]
    line_chart_data: List[Dict[str, Any]] = []
    
    # 상세 페이지 데이터: 선택된 날짜의 상위 30개 단어
    detail_data: List[WordCount] = []
    
    # 요약 기사 데이터: 선택된 날짜의 요약 기사들
    summary_data: List[SummaryItem] = []
    
    # 페이지네이션 관련
    current_summary_page: int = 1
    items_per_page: int = 20
    
    # 필터링 관련
    selected_category: str = "전체"
    
    @rx.var
    def available_categories(self) -> List[str]:
        """사용 가능한 분류 목록 반환 (전체 + 고유 분류들)"""
        if not self.summary_data:
            return ["전체"]
        categories = set(item["category"] for item in self.summary_data)
        return ["전체"] + sorted(list(categories))
    
    @rx.var
    def filtered_summary_data(self) -> List[SummaryItem]:
        """선택된 분류에 따라 필터링된 데이터 반환"""
        if self.selected_category == "전체":
            return self.summary_data
        return [item for item in self.summary_data if item["category"] == self.selected_category]
    
    @rx.var
    def total_summary_pages(self) -> int:
        """전체 페이지 수 계산 (필터링된 데이터 기준)"""
        filtered_count = len(self.filtered_summary_data)
        if filtered_count == 0:
            return 1
        return (filtered_count + self.items_per_page - 1) // self.items_per_page
    
    @rx.var
    def paginated_summary_data(self) -> List[SummaryItem]:
        """현재 페이지에 해당하는 요약 데이터 반환 (필터링된 데이터 기준)"""
        filtered = self.filtered_summary_data
        start_idx = (self.current_summary_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        return filtered[start_idx:end_idx]
    
    def set_category_filter(self, category: str):
        """분류 필터 설정 및 페이지 리셋"""
        self.selected_category = category
        self.current_summary_page = 1  # 필터 변경 시 1페이지로 리셋
    
    def go_to_summary_page(self, page_num: int):
        """특정 페이지로 이동"""
        if 1 <= page_num <= self.total_summary_pages:
            self.current_summary_page = page_num
    
    def next_summary_page(self):
        """다음 페이지로 이동"""
        if self.current_summary_page < self.total_summary_pages:
            self.current_summary_page += 1
    
    def prev_summary_page(self):
        """이전 페이지로 이동"""
        if self.current_summary_page > 1:
            self.current_summary_page -= 1

    def get_latest_csv_files(self, rank_folder: Path, max_files: int = 7) -> List[Path]:
        """
        rank 폴더에서 최신 파일들을 가져오기
        
        Args:
            rank_folder: CSV 파일들이 있는 폴더 경로
            max_files: 가져올 최대 파일 개수 (기본값: 7)
            
        Returns:
            List[Path]: 최신 CSV 파일 경로 리스트
        """
        if not rank_folder or not rank_folder.exists():
            print(f"✗ Rank folder does not exist: {rank_folder}")
            return []
        
        # 1. CSV 파일들을 모두 가져오기
        all_csv_files = list(rank_folder.glob("*.csv"))
        print(f"Found {len(all_csv_files)} CSV files in total")
        
        if not all_csv_files:
            return []
        
        # 2. 파일명 기준으로 오름차순 정렬 (yyyymmdd.csv)
        sorted_csv_files = sorted(all_csv_files, key=lambda f: f.stem)
        
        # 3. 최신 max_files개 파일만 선택 (마지막 max_files개)
        latest_files = sorted_csv_files[-max_files:] if len(sorted_csv_files) > max_files else sorted_csv_files
        print(f"Processing latest {len(latest_files)} CSV files")
        
        return latest_files
    
    def extract_card_data_from_csv(self, csv_file: Path, max_words: int = 10) -> Dict[str, Any] | None:
        """
        CSV 파일에서 카드 데이터 추출
        
        Args:
            csv_file: CSV 파일 경로
            max_words: 추출할 최대 단어 개수 (기본값: 10)
            
        Returns:
            Dict[str, Any] | None: {"date": "20251025", "value": [(word, count), ...]} 또는 None
        """
        try:
            # 파일명에서 날짜 추출 (예: 20251025.csv)
            date_str = csv_file.stem  # 확장자 제외한 파일명
            print(f"Processing file: {csv_file.name}")
            
            if len(date_str) != 8:  # yyyymmdd 형식이 아니면 건너뜀
                return None
            
            word_count_list = []
            
            # CSV 파일 읽기
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                
                # 첫 번째 줄(헤더) 건너뛰기
                next(reader, None)
                
                # 상위 max_words개의 데이터 읽기
                for i, row in enumerate(reader):
                    if i >= max_words:
                        break
                    if row and len(row) >= 2:
                        word = row[0]
                        count = row[1]
                        word_count_list.append((word, count))
                
                if word_count_list:
                    print(f"  → {date_str}: {len(word_count_list)} words extracted")
                    return {
                        "date": date_str,
                        "value": word_count_list
                    }
                else:
                    print(f"  → No data found in {csv_file.name}")
                    return None
                    
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
            return None
    
    def extract_kpi_from_csv(self, csv_file: Path) -> Dict[str, str] | None:
        """
        CSV 파일에서 KPI 데이터 추출
        
        Args:
            csv_file: CSV 파일 경로
            
        Returns:
            Dict[str, str] | None: {"title", "word", "count"} 딕셔너리 또는 None
        """
        try:
            # 파일명에서 날짜 추출 (예: 20251025.csv -> 10/25)
            date_str = csv_file.stem  # 확장자 제외한 파일명
            print(f"Processing file: {csv_file.name} -> {date_str}")
            
            if len(date_str) != 8:  # yyyymmdd 형식이 아니면 건너뜀
                return None
                
            mm = date_str[4:6]
            dd = date_str[6:8]
            formatted_date = f"{mm}/{dd}"
            
            # CSV 파일 읽기
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                
                # 첫 번째 줄(헤더) 건너뛰기
                next(reader, None)
                
                # 두 번째 줄(첫 번째 데이터) 읽기
                first_row = next(reader, None)
                
                if first_row and len(first_row) >= 2:
                    word = first_row[0]
                    count = first_row[1]
                    
                    print(f"  → {formatted_date}: word='{word}', count='{count}'")
                    
                    return {
                        "title": formatted_date,
                        "word": word,
                        "count": count
                    }
                else:
                    print(f"  → No data found in {csv_file.name}")
                    return None
                    
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
            return None
    
    def load_rank_files(self):
        """rank 폴더의 파일명을 읽어서 모든 데이터 생성"""
        print("=== load_rank_files() 호출됨 ===")
        
        # 1. 데이터가 있는 폴더 
        possible_paths = [
            Path(__file__).parent / "res" / "rank",
        ]
        
        rank_folder = None
        for path in possible_paths:
            print(f"Trying path: {path}")
            if path.exists():
                rank_folder = path
                print(f"✓ Found folder at: {path}")
                break
               
        # 2. 최신 7개 파일 가져오기
        csv_files = self.get_latest_csv_files(rank_folder, max_files=7)
        
        # 3. 데이터 저장용 변수들
        card_items = []  # 카드용
        heatmap_dict = {}  # 히트맵용 (날짜 → {단어: 빈도수})
        line_chart_dict = {}  # 라인 차트용 (날짜별로 단어 집계)
        all_words_by_date = {}  # 각 날짜의 전체 단어 리스트
       
        for csv_file in csv_files:
            # 파일명에서 날짜 추출 (예: 20251020.csv)
            date_str = csv_file.stem
            print(f"Processing file: {csv_file.name}")
            
            try:
                # CSV 파일 읽기
                with open(csv_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    
                    # 첫 번째 줄(헤더) 건너뛰기
                    next(reader, None)
                    
                    # 모든 데이터를 한 번에 읽기
                    all_words = []
                    for row in reader:
                        if row and len(row) >= 2:
                            word = row[0]
                            count = int(row[1])
                            all_words.append({"word": word, "count": count})
                    
                    all_words_by_date[date_str] = all_words
                    
                    # 카드용: 상위 4개만
                    words_list_for_card = [
                        {"word": w["word"], "count": str(w["count"])} 
                        for w in all_words[:4]
                    ]
                    
                    if words_list_for_card:
                        card_items.append({
                            "date": date_str,
                            "words": words_list_for_card
                        })
                    
                    # 히트맵용: 날짜별 단어-빈도 딕셔너리
                    word_dict = {}
                    for item in all_words[:30]:
                        word_dict[item["word"]] = item["count"]
                    heatmap_dict[date_str] = word_dict
                    
                    # 라인 차트용: 상위 10개 단어
                    line_data = {"date": date_str}
                    for item in all_words[:10]:
                        line_data[item["word"]] = item["count"]
                    line_chart_dict[date_str] = line_data
                                
                print(f"  → {date_str}: {len(all_words)}개 단어 추출 완료")
                        
            except Exception as e:
                print(f"Error processing {csv_file}: {e}")
                continue
        
        # 4. 히트맵 데이터 생성 - 첫 번째 날짜의 상위 20개 단어 기준
        heatmap_items = []
        if all_words_by_date:
            # 첫 번째 날짜의 상위 20개 단어를 기준으로 사용
            first_date = sorted(all_words_by_date.keys())[0]
            top_20_words = [w["word"] for w in all_words_by_date[first_date][:20]]
            
            # 각 날짜별로 이 20개 단어의 빈도수 수집
            for date_str in sorted(heatmap_dict.keys()):
                word_counts = heatmap_dict[date_str]
                for word in top_20_words:
                    count = word_counts.get(word, 0)  # 없으면 0
                    heatmap_items.append({
                        "date": date_str,
                        "word": word,
                        "count": count
                    })
        
        # 5. 라인 차트 데이터 정리
        line_chart_items = []
        for date_str in sorted(line_chart_dict.keys()):
            line_chart_items.append(line_chart_dict[date_str])
        
        # 6. 데이터 저장
        self.card_data = card_items
        self.heatmap_data = heatmap_items
        self.line_chart_data = line_chart_items
               
        print(f"Total Card items loaded: {len(self.card_data)} 날짜")
        print(f"Total Heatmap items loaded: {len(self.heatmap_data)} 데이터 포인트")
        print(f"Total Line chart items loaded: {len(self.line_chart_data)} 날짜")
              
        # 디버깅: 처음 2개 카드 데이터 출력
        if self.card_data:
            print("First 2 card data items:")
            for i, item in enumerate(self.card_data[:2]):
                print(f"  {i+1}: {item['date']} - {len(item['words'])}개 단어")
        
        
    
    def change_page(self, page: str):
        """메뉴 클릭 시 페이지 상태 업데이트"""
        self.current_page = page
        self.selected_date = ""
    
    def select_date(self, date: str):
        """날짜 선택 시 해당 날짜 페이지로 이동"""
        self.current_page = "Detail"
        self.selected_date = date
        print(f"Selected date: {date}")
        # 선택된 날짜의 상세 데이터 로드
        self.load_detail_data(date)
    
    def load_detail_data(self, date: str):
        """선택된 날짜의 상세 데이터 로드 (상위 30개 단어)"""
        # res/rank 폴더 경로 설정
        current_file = Path(__file__)
        project_root = current_file.parent  # WebProgram/WebProgram 폴더
        rank_folder = project_root / "res" / "rank"
        
        # 해당 날짜의 CSV 파일 찾기
        csv_file = rank_folder / f"{date}.csv"
        
        if not csv_file.exists():
            print(f"✗ CSV file not found: {csv_file}")
            self.detail_data = []
            return
        
        print(f"Loading detail data from: {csv_file}")
        detail_words = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None)  # 헤더 건너뛰기
                
                # 상위 30개 단어 읽기
                for i, row in enumerate(reader):
                    if i >= 30:
                        break
                    if row and len(row) >= 2:
                        detail_words.append(WordCount(word=row[0], count=row[1]))
            
            self.detail_data = detail_words
            print(f"✓ Loaded {len(detail_words)} words for detail page")
            
        except Exception as e:
            print(f"✗ Error loading detail data: {e}")
            self.detail_data = []
    
    def select_summary(self, date: str):
        """요약 기사 페이지로 이동"""
        self.current_page = "Summary"
        self.selected_date = date
        self.current_summary_page = 1  # 페이지를 1로 리셋
        self.selected_category = "전체"  # 분류 필터 리셋
        print(f"Selected summary for date: {date}")
        # 선택된 날짜의 요약 데이터 로드
        self.load_summary_data(date)
    
    def load_summary_data(self, date: str):
        """선택된 날짜의 요약 기사 데이터 로드"""
        # res/summary 폴더 경로 설정
        current_file = Path(__file__)
        project_root = current_file.parent  # WebProgram/WebProgram 폴더
        summary_folder = project_root / "res" / "summary"
        
        # 해당 날짜의 .sum 파일 찾기
        summary_file = summary_folder / f"{date}.sum"
        
        if not summary_file.exists():
            print(f"✗ Summary file not found: {summary_file}")
            self.summary_data = []
            return
        
        print(f"Loading summary data from: {summary_file}")
        summaries = []
        
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 각 라인 처리
            lines = content.split('\n')
            current_category = ""
            current_summary = ""
            
            for line in lines:
                line = line.strip()
                
                # 코드 블록 마커 무시
                if line.startswith('```') or line.startswith('````'):
                    continue
                
                # 분류 라인 처리
                if line.startswith('<분류>:'):
                    # 이전 항목 저장
                    if current_category and current_summary:
                        summaries.append(SummaryItem(category=current_category, summary=current_summary))
                    # 새 항목 시작
                    current_category = line.replace('<분류>:', '').strip()
                    current_summary = ""
                
                # 요약 라인 처리
                elif line.startswith('<요약>:'):
                    current_summary = line.replace('<요약>:', '').strip()
            
            # 마지막 항목 저장
            if current_category and current_summary:
                summaries.append(SummaryItem(category=current_category, summary=current_summary))
            
            self.summary_data = summaries
            print(f"✓ Loaded {len(summaries)} summary items")
            
        except Exception as e:
            print(f"✗ Error loading summary data: {e}")
            self.summary_data = []
    
    @rx.var
    def chart_data_list(self) -> list:
        """차트용 데이터 변환"""
        return [
            {
                "label": f"{item['word']}",
                "count": int(item['count'])
            }
            for item in self.kpi_data
        ]
    
    @rx.var
    def heatmap_chart_config(self) -> dict:
        """히트맵 차트 설정 반환"""
        if not self.heatmap_data:
            return {"data": [], "layout": {}}
        
        # 날짜와 단어 리스트 추출
        dates = sorted(list(set([item["date"] for item in self.heatmap_data])))
        words = []
        seen_words = set()
        for item in self.heatmap_data:
            if item["word"] not in seen_words:
                words.append(item["word"])
                seen_words.add(item["word"])
        
        # 디버깅
        print(f"히트맵 날짜: {dates}")
        print(f"히트맵 단어 개수: {len(words)}")
        print(f"히트맵 첫 5개 단어: {words[:5]}")
        
        # 히트맵용 2D 배열 생성
        z_data = []
        for word in words:
            row = []
            for date in dates:
                # 해당 날짜의 해당 단어 빈도수 찾기
                count = 0
                for item in self.heatmap_data:
                    if item["word"] == word and item["date"] == date:
                        count = item["count"]
                        break
                row.append(count)
            z_data.append(row)
        
        print(f"히트맵 z_data 크기: {len(z_data)} x {len(z_data[0]) if z_data else 0}")
        print(f"히트맵 첫 행 샘플: {z_data[0][:3] if z_data else []}")
        
        return {
            "data": [{
                "type": "heatmap",
                "z": z_data,
                "x": dates,
                "y": words,
                "colorscale": "YlOrRd",
                "hoverongaps": False,
                "showscale": True
            }],
            "layout": {
                "title": "단어별 빈도수 히트맵",
                "xaxis": {"title": "날짜"},
                "yaxis": {"title": "단어", "autorange": "reversed"},
                "height": 600,
                "margin": {"l": 100, "r": 50, "t": 50, "b": 50}
            }
        }
    
    @rx.var
    def line_chart_config(self) -> dict:
        """라인 차트 설정 반환"""
        if not self.line_chart_data:
            return {"data": [], "layout": {}}
        
        # 모든 단어 추출 (date 제외)
        all_words = set()
        for item in self.line_chart_data:
            for key in item.keys():
                if key != "date":
                    all_words.add(key)
        
        # 상위 5개 단어만 선택 (첫 번째 날짜 기준)
        if self.line_chart_data:
            first_day = self.line_chart_data[0]
            word_counts = [(word, first_day.get(word, 0)) for word in all_words]
            word_counts.sort(key=lambda x: x[1], reverse=True)
            top_words = [word for word, _ in word_counts[:5]]
        else:
            top_words = list(all_words)[:5]
        
        print(f"라인 차트 상위 단어: {top_words}")
        print(f"라인 차트 날짜 개수: {len(self.line_chart_data)}")
        
        # 각 단어별 데이터 라인 생성
        traces = []
        for word in top_words:
            x_values = [item["date"] for item in self.line_chart_data]
            y_values = [item.get(word, 0) for item in self.line_chart_data]
            print(f"  {word}: {y_values}")
            traces.append({
                "type": "scatter",
                "mode": "lines+markers",
                "name": word,
                "x": x_values,
                "y": y_values,
                "line": {"width": 2},
                "marker": {"size": 8}
            })
        
        return {
            "data": traces,
            "layout": {
                "title": "키워드별 빈도수 추이",
                "xaxis": {"title": "날짜"},
                "yaxis": {"title": "빈도수"},
                "height": 400,
                "showlegend": True,
                "hovermode": "closest"
            }
        }


def dashboard_content() -> rx.Component:
    """대시보드 페이지 콘텐츠"""
    return rx.vstack(
        # 현재 선택된 페이지 제목 표시
        rx.heading(
            "Dashboard",
            size="8",
        ),
        # 페이지 설명 텍스트
        rx.text(
            "See One Week's economic news data",
            color="gray.500",
            margin_bottom="1em",
        ),
        
        # 데이터 개수 표시
        rx.text(
            rx.cond(
                State.card_data.length() > 0,
                f"최근 {State.card_data.length()}일의 데이터가 있습니다.",
                "데이터를 로딩 중입니다..."
            ),
            font_size="16px", 
            margin_bottom="1em"
        ),
        
        # 카드 컨테이너 (날짜별 카드 - 4열 그리드)
        rx.grid(
            rx.foreach(
                State.card_data,
                lambda card: rx.card(
                    rx.vstack(
                        # 상단: 날짜(좌측) + 아이콘들(우측)
                        rx.hstack(
                            rx.text(
                                card["date"], 
                                font_size="14px", 
                                font_weight="bold", 
                                color="blue.600",
                            ),
                            rx.hstack(
                                rx.tooltip(
                                    rx.icon(
                                        "external-link",
                                        size=18,
                                        color="gray.500",
                                        cursor="pointer",
                                        on_click=lambda: State.select_date(card["date"]),
                                        _hover={"color": "blue.600"}
                                    ),
                                    content="상세 순위",
                                ),
                                rx.tooltip(
                                    rx.icon(
                                        "file-text",
                                        size=18,
                                        color="gray.500",
                                        cursor="pointer",
                                        on_click=lambda: State.select_summary(card["date"]),
                                        _hover={"color": "green.600"}
                                    ),
                                    content="요약 기사",
                                ),
                                spacing="2",
                            ),
                            justify="between",
                            width="100%",
                            margin_bottom="12px"
                        ),
                        # 단어들을 세로로 나열
                        rx.foreach(
                            card["words"],
                            lambda word_item: rx.hstack(
                                rx.text(
                                    word_item["word"], 
                                    font_size="16px",
                                    font_weight="500",
                                    width="120px"
                                ),
                                rx.text(
                                    word_item["count"], 
                                    font_size="16px",
                                    color="gray.600"
                                ),
                                spacing="3",
                                width="100%"
                            )
                        ),
                        align="start",
                        spacing="2",
                        width="100%"
                    ),
                    padding="20px",
                    border="1px solid #e2e8f0",
                    border_radius="8px",
                    _hover={"border_color": "blue.300", "box_shadow": "lg"}
                )
            ),
            columns="4",
            spacing="4",
            width="100%"
        ),
        
        # 구분선
        rx.divider(margin_top="2em", margin_bottom="2em"),
        
        # 차트 섹션 제목
        rx.heading("데이터 추이 분석", size="6", margin_bottom="1em"),
        
        # 라인 차트 섹션 (Recharts 사용)
        rx.box(
            rx.heading("라인 차트: 상위 키워드 추이", size="4", margin_bottom="1em"),
            rx.text(
                "상위 5개 핵심 키워드의 시계열 변화를 추적합니다.",
                color="gray.600",
                font_size="14px",
                margin_bottom="1em"
            ),
            rx.cond(
                State.line_chart_data.length() > 0,
                rx.recharts.line_chart(
                    rx.recharts.line(
                        data_key="금융",
                        stroke="#8884d8",
                        type_="monotone",
                    ),
                    rx.recharts.line(
                        data_key="대출",
                        stroke="#82ca9d",
                        type_="monotone",
                    ),
                    rx.recharts.line(
                        data_key="은행",
                        stroke="#ffc658",
                        type_="monotone",
                    ),
                    rx.recharts.line(
                        data_key="서울",
                        stroke="#ff7c7c",
                        type_="monotone",
                    ),
                    rx.recharts.line(
                        data_key="투자",
                        stroke="#8dd1e1",
                        type_="monotone",
                    ),
                    rx.recharts.x_axis(data_key="date"),
                    rx.recharts.y_axis(),
                    rx.recharts.legend(),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    data=State.line_chart_data,
                    width="100%",
                    height=400,
                ),
                rx.text("라인 차트 데이터를 로딩 중...", color="gray.500")
            ),
            width="100%",
            margin_bottom="2em"
        ),
        
        # 바 차트 섹션 (히트맵 대신)
        rx.box(
            rx.heading("바 차트: 날짜별 상위 단어 비교", size="4", margin_bottom="1em"),
            rx.text(
                "각 날짜별 상위 5개 단어의 빈도수를 막대 그래프로 비교합니다.",
                color="gray.600",
                font_size="14px",
                margin_bottom="1em"
            ),
            rx.cond(
                State.line_chart_data.length() > 0,
                rx.recharts.bar_chart(
                    rx.recharts.bar(
                        data_key="금융",
                        fill="#8884d8",
                    ),
                    rx.recharts.bar(
                        data_key="대출",
                        fill="#82ca9d",
                    ),
                    rx.recharts.bar(
                        data_key="은행",
                        fill="#ffc658",
                    ),
                    rx.recharts.bar(
                        data_key="서울",
                        fill="#ff7c7c",
                    ),
                    rx.recharts.bar(
                        data_key="투자",
                        fill="#8dd1e1",
                    ),
                    rx.recharts.x_axis(data_key="date"),
                    rx.recharts.y_axis(),
                    rx.recharts.legend(),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    data=State.line_chart_data,
                    width="100%",
                    height=400,
                ),
                rx.text("바 차트 데이터를 로딩 중...", color="gray.500")
            ),
            width="100%"
        ),
       
        align_items="flex-start",
        width="100%",
        padding="2em",
    )

def detail_page_content() -> rx.Component:
    """상세 페이지 콘텐츠 - 선택된 날짜의 상위 30개 단어 표시"""
    return rx.vstack(
        # 페이지 헤더 (뒤로가기 버튼 + 날짜 제목)
        rx.hstack(
            rx.icon_button(
                rx.icon("arrow-left"),
                size="2",
                cursor="pointer",
                on_click=lambda: State.change_page("Dashboard"),
                variant="soft",
            ),
            rx.heading(
                rx.text.span("날짜별 상세 분석: ", color="gray.600", font_size="1.8em"),
                rx.text.span(State.selected_date, color="rgb(107, 139, 255)", font_size="1.8em"),
                size="8",
                mb="0",
            ),
            align_items="center",
            spacing="3",
            width="100%",
            padding_bottom="1em",
        ),
        
        # 상위 30개 단어 테이블
        rx.heading("상위 30개 키워드", size="6", color="gray.700", padding_bottom="0.5em"),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("순위", width="15%"),
                        rx.table.column_header_cell("단어", width="50%"),
                        rx.table.column_header_cell("빈도수", width="35%"),
                    ),
                ),
                rx.table.body(
                    rx.foreach(
                        State.detail_data,
                        lambda word_data, index: rx.table.row(
                            rx.table.cell(
                                rx.badge(
                                    f"#{index + 1}",
                                    color_scheme="blue",
                                    size="2",
                                ),
                            ),
                            rx.table.cell(
                                rx.text(
                                    word_data["word"],
                                    font_size="1.1em",
                                    font_weight="600",
                                    color="gray.800",
                                ),
                            ),
                            rx.table.cell(
                                rx.text(
                                    word_data["count"],
                                    font_size="1em",
                                    font_weight="500",
                                    color="rgb(107, 139, 255)",
                                ),
                            ),
                            _hover={"bg": "gray.50"},
                        ),
                    ),
                ),
                variant="surface",
                size="3",
                width="100%",
            ),
            width="100%",
            padding_bottom="2em",
        ),
        
        # 바 차트: 상위 30개 단어 시각화
        rx.heading("빈도수 차트", size="6", color="gray.700", padding_top="1em", padding_bottom="0.5em"),
        rx.box(
            rx.cond(
                State.detail_data.length() > 0,
                rx.recharts.bar_chart(
                    rx.recharts.bar(
                        data_key="count",
                        fill="#8884d8",
                    ),
                    rx.recharts.x_axis(
                        data_key="word",
                        angle=-45,
                        text_anchor="end",
                        height=100,
                    ),
                    rx.recharts.y_axis(),
                    rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                    data=State.detail_data,
                    width="100%",
                    height=500,
                ),
                rx.text("데이터를 로딩 중...", color="gray.500")
            ),
            width="100%"
        ),
        
        align_items="flex-start",
        width="100%",
        padding="2em",
    )

def summary_page_content() -> rx.Component:
    """요약 기사 페이지 콘텐츠 - 선택된 날짜의 요약 기사들 표시"""
    return rx.vstack(
        # 페이지 헤더 (뒤로가기 버튼 + 날짜 제목)
        rx.hstack(
            rx.icon_button(
                rx.icon("arrow-left"),
                size="2",
                cursor="pointer",
                on_click=lambda: State.change_page("Dashboard"),
                variant="soft",
            ),
            rx.heading(
                rx.text.span("요약 기사: ", color="gray.600", font_size="1.8em"),
                rx.text.span(State.selected_date, color="rgb(107, 139, 255)", font_size="1.8em"),
                size="8",
                mb="0",
            ),
            align_items="center",
            spacing="3",
            width="100%",
            padding_bottom="1em",
        ),
        
        # 분류 필터 및 통계
        rx.hstack(
            rx.vstack(
                rx.text("분류 필터:", font_weight="600", color="gray.700", font_size="0.9em"),
                rx.select(
                    State.available_categories,
                    value=State.selected_category,
                    on_change=State.set_category_filter,
                    size="2",
                ),
                spacing="1",
                align_items="flex-start",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text("전체:", font_weight="500", color="gray.600", font_size="0.9em"),
                    rx.badge(f"{State.summary_data.length()}개", color_scheme="blue", size="2"),
                    spacing="2",
                ),
                rx.hstack(
                    rx.text("필터링:", font_weight="500", color="gray.600", font_size="0.9em"),
                    rx.badge(f"{State.filtered_summary_data.length()}개", color_scheme="green", size="2"),
                    spacing="2",
                ),
                spacing="1",
                align_items="flex-start",
            ),
            spacing="6",
            align_items="flex-start",
            padding_bottom="1em",
            width="100%",
        ),
        
        # 페이지 정보
        rx.hstack(
            rx.text(
                f"페이지 {State.current_summary_page} / {State.total_summary_pages}",
                color="gray.600",
                font_size="0.9em",
            ),
            spacing="3",
            align_items="center",
            padding_bottom="0.5em",
        ),
        rx.box(
            rx.cond(
                State.summary_data.length() > 0,
                rx.vstack(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("번호", width="10%"),
                                rx.table.column_header_cell("분류", width="20%"),
                                rx.table.column_header_cell("요약", width="70%"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                State.paginated_summary_data,
                                lambda summary_item, index: rx.table.row(
                                    rx.table.cell(
                                        rx.text(
                                            f"{(State.current_summary_page - 1) * State.items_per_page + index + 1}",
                                            font_weight="500",
                                            color="gray.600",
                                        ),
                                    ),
                                    rx.table.cell(
                                        rx.badge(
                                            summary_item["category"],
                                            color_scheme="green",
                                            size="2",
                                        ),
                                    ),
                                    rx.table.cell(
                                        rx.text(
                                            summary_item["summary"],
                                            font_size="0.95em",
                                            line_height="1.6",
                                            color="gray.700",
                                        ),
                                    ),
                                    _hover={"bg": "gray.50"},
                                ),
                            ),
                        ),
                        variant="surface",
                        size="3",
                        width="100%",
                    ),
                    # 페이지네이션 컨트롤
                    rx.hstack(
                        rx.button(
                            rx.icon("chevron-left"),
                            on_click=State.prev_summary_page,
                            disabled=State.current_summary_page == 1,
                            variant="soft",
                            size="2",
                        ),
                        rx.text(
                            f"{State.current_summary_page} / {State.total_summary_pages}",
                            font_size="0.9em",
                            color="gray.700",
                        ),
                        rx.button(
                            rx.icon("chevron-right"),
                            on_click=State.next_summary_page,
                            disabled=State.current_summary_page >= State.total_summary_pages,
                            variant="soft",
                            size="2",
                        ),
                        spacing="3",
                        justify="center",
                        width="100%",
                        padding_top="1em",
                    ),
                    width="100%",
                    spacing="0",
                ),
                rx.text("데이터를 로딩 중...", color="gray.500")
            ),
            width="100%",
            padding_bottom="2em",
        ),
        
        align_items="flex-start",
        width="100%",
        padding="2em",
    )

def sidebar() -> rx.Component:
    # 왼쪽 네비게이션 사이드바 생성
    return rx.box(
        rx.vstack(
            # 앱 로고 표시 (아이콘 + 텍스트)
            rx.hstack(
                rx.icon("eye", color="rgb(107, 139, 255)", mr="2"),
                rx.heading("SeeFlow", size="8", mb="0"),
                align_items="center",
            ),
            
            # 대시보드 메뉴
            rx.hstack(
                rx.icon("layout-grid", color="rgb(107, 139, 255)", mr="2"),
                rx.heading(
                    "Dashboard",
                    size="5",
                    cursor="pointer",
                    on_click=lambda: State.change_page("Dashboard"),
                    _hover={"color": "rgb(80, 110, 200)"},
                ),
                align_items="center",
                padding_left="12px",
            ),
            align_items="flex-start",
            width="100%",
            spacing="4",
        ),
        min_height="100vh",
        p="4",
        border_right="0.5px solid",
        border_color="rgb(220, 220, 220)",
        width="250px",
    )

def main_content() -> rx.Component:
    """메인 콘텐츠 - 현재 페이지에 따라 다른 콘텐츠 표시"""
    return rx.scroll_area(
        rx.cond(
            State.current_page == "Dashboard",
            dashboard_content(),
            rx.cond(
                State.current_page == "Detail",
                detail_page_content(),
                rx.cond(
                    State.current_page == "Summary",
                    summary_page_content(),
                    dashboard_content(),  # 기본값
                ),
            ),
        ),
        type_="always",
        scrollbars="vertical",
        style={"height": "100vh"},
        bg="rgba(240, 240, 240, 0.5)",
    )

def index() -> rx.Component:
    # 메인 레이아웃 구성 - 사이드바와 콘텐츠 영역을 수평으로 배치
    return rx.hstack(
        sidebar(),
        main_content(),
        width="100%",
        height="100vh",
        spacing="0",
        on_mount=State.load_rank_files,  # 페이지 로드 시 데이터 로드
    )

# Reflex 앱 초기화 및 라우트 설정
app = rx.App()
app.add_page(index)