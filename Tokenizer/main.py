import os
from kiwipiepy import Kiwi
from pathlib import Path
import json
from datetime import datetime

def gen_word_count(kiwi: Kiwi, text: str) -> dict:    
    # tokenize로 형태소 분석
    tokens = kiwi.tokenize(text)
    
    # 명사 카운트를 저장할 딕셔너리
    noun_counts = {}
    
    # 각 토큰에 대해 명사인 경우만 카운트
    for token in tokens:
        # 품사가 N으로 시작하면 명사
        if token.tag.startswith('N'):
            noun = token.form
            # 2음절 이상인 명사만 카운트 (한글 한 글자는 보통 1음절)
            if len(noun) >= 2:
                noun_counts[noun] = noun_counts.get(noun, 0) + 1
    
    return noun_counts

# 주어진 폴더 내 모든 텍스트 파일의 워드 카운트를 생성
# data_dir: 텍스트 파일이 들어있는 경로. yymmdd 형식의 폴더.
# 이 폴더 내 여러 텍스트 파일을 모두 처리함.
def word_count_for_folder(data_dir: Path) -> dict:
    """
    폴더 내 모든 텍스트 파일의 통합 워드 카운트를 생성

    Args:
        data_dir (Path): 텍스트 파일들이 있는 폴더 경로

    Returns:
        dict: 통합된 {단어: 출현횟수} 딕셔너리
    """
    # Kiwi 초기화
    kiwi = Kiwi()
    
    # 통합 워드 카운트 딕셔너리
    merged_counts = {}
    
    # 폴더 내 모든 .txt 파일 처리
    for txt_file in data_dir.glob('*.txt'):
        try:
            # 파일 읽기
            text = txt_file.read_text(encoding='utf-8')
            
            # 현재 파일의 워드 카운트 추출
            current_counts = gen_word_count(kiwi, text)
            
            # 현재 파일의 카운트를 통합 딕셔너리에 병합
            for word, count in current_counts.items():
                merged_counts[word] = merged_counts.get(word, 0) + count
                
        except Exception as e:
            print(f"Error processing {txt_file}: {e}")
            continue
    
    return merged_counts

# 딕셔너리를 받아서 파일로 저장하는 함수
# data_str: 날짜 문자열 (yymmdd 형식)
# word_dic: 단어 카운트 딕셔너리
def save_word_count_to_file(data_str: str, word_dic: dict, max_rank: int = None) -> Path:
    """
    data_str: yyyymmdd 형식의 문자열
    word_dic: {word: count} 딕셔너리
    max_rank: 저장할 상위 개수 (None 또는 <=0이면 전체 저장)
    Tokenizer 폴더 내 data 폴더에 yyyymmdd.csv 파일로 저장 (utf-8-sig)
    """
    import csv

    output_dir = Path(__file__).parent / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{data_str}.csv"
    path = output_dir / filename

    # 정렬: 카운트 내림차순, 동일하면 단어 오름차순
    items = sorted(word_dic.items(), key=lambda x: (-x[1], x[0]))

    # max_rank가 유효한 정수이면 그 수만큼 자르기
    if isinstance(max_rank, int) and max_rank > 0:
        items = items[:max_rank]

    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['word', 'count'])
        for word, count in items:
            writer.writerow([word, count])

    return path

def main():
    import sys

    max_rank = 30   

    # 1. 소스폴더 경로 설정. article_dir: Downloader/Data
    article_dir = Path(__file__).parent.parent / 'Downloader' / 'Data'
    if not article_dir.exists():
        print(f"Article data dir not found: {article_dir}")
        return

    # 2. 소스폴더 내 모든 폴더 순회 (폴더명은 yyyymmdd 형식)
    for sub in sorted(article_dir.iterdir()):
        if not sub.is_dir():
            continue
        data_str = sub.name
        # 폴더명이 yyyymmdd 형식이 아니면 건너뜀
        if not (len(data_str) == 8 and data_str.isdigit()):
            continue

        print(f"Processing date folder: {data_str}")

        # 3. 각 폴더별로 word_count_for_folder 실행하고 CSV로 저장
        try:
            merged_counts = word_count_for_folder(sub)
        except Exception as e:
            print(f"Error counting words in {sub}: {e}")
            continue

        if not merged_counts:
            print(f"No words found in {sub}, skipping save.")
            continue

        try:
            out_path = save_word_count_to_file(data_str, merged_counts, max_rank)
            print(f"Saved word counts to: {out_path}")
        except Exception as e:
            print(f"Error saving CSV for {data_str}: {e}")

if __name__ == "__main__":
    main()
