import google.generativeai as genai
import os

NEWS_DATA_DIR = "./Downloader/data/"
SUMMARIZED_DATA_DIR = "./Summarizer/data/"

# Gemini의 모델을 생성한다.
def get_single_summary_model():
    # 1. API 키 설정
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


    # 2. model 설정
    instructions = """
    아래는 금융 뉴스 기사입니다.
    이 뉴스 기사를 <분류>로 구분하고 <요약>을 해주세요.
    <분류>는 나중에 이 뉴스들을 그룹화할 때 사용할 것입니다.
    <요약>은 뉴스의 핵심 내용을 간결하게 전달하는 문장이어야 합니다.


    [출력 형식]
    <분류>: [여기에 분류 입력]
    <요약>: [여기에 요약 입력]
    ---------------
    """
    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=instructions)


    return model

# 파라미터로 주어진 텍스트파일에 대해 Gemini에 요약을 요청하고 결과를 반환한다.
# model: Gemini 모델 객체
# file_path: 요약할 텍스트 파일 경로
# def summarize_article(model, file_path):
def summarize_article(model, file_path):
    try:
        # 텍스트 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Gemini 모델을 사용하여 요약 생성
        response = model.generate_content(content)

        summary = response.text.strip()

        return summary    
    
    
    except FileNotFoundError:
        print(f"오류: {file_path}에서 파일을 찾을 수 없습니다")
        return None
    except Exception as e:
        print(f"기사 처리 중 오류 발생: {str(e)}")
        return None

# 요약들을 모아서 Gemini에 종합 요약을 요청한다.
# model: Gemini 모델 객체
# summaries: 요약문 리스트
def summarize_all_articles(summaries):
    try:
        # 1. API 키 설정
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # 2. 모델 설정
        instructions = """
        주어진 요약문자는 다음과 같은 형태입니다.
        <분류>: [여기에 분류 입력]
        <요약>: [여기에 요약 입력]
        ---------------
        이를 이용해서 <분류> 별로 전체 내용을 종합요약해주세요
        """
        
        model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=instructions)

        # 3. 모든 요약문을 하나의 문자열로 결합
        combined_summaries = "\n".join(summaries)

        # 4. Gemini 모델을 사용하여 종합 요약 생성
        response = model.generate_content(combined_summaries)
        
        # 5. 응답에서 텍스트 추출 및 반환
        final_summary = response.text.strip()
        return final_summary

    except Exception as e:
        print(f"종합 요약 생성 중 오류 발생: {str(e)}")
        return None

def main():
    # 1. API 키 확인
    if not os.getenv("GOOGLE_API_KEY"):
        print("GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
        return
    
    # 2. 각 기사별 요약용 모델 생성
    model = get_single_summary_model()

    # 3. 소스폴더 경로 설정. 없으면 에러
    if not os.path.exists(NEWS_DATA_DIR):
        print(f"오류: {NEWS_DATA_DIR} 폴더를 찾을 수 없습니다.")
        return
    
    # 4. NEWS_DATA_DIR 폴더 밑에 있는 모든 폴더를 순회 (날짜별 폴더)
    for date_folder in os.listdir(NEWS_DATA_DIR):
        date_path = os.path.join(NEWS_DATA_DIR, date_folder)
        if not os.path.isdir(date_path):
            continue

        print(f"\n{date_folder} 폴더 처리 중...")
        daily_summaries = []

        # 5. 각 폴더의 모든 텍스트파일에 대해 요약. 하루치
        for file_name in os.listdir(date_path):
            if not file_name.endswith('.txt'):
                continue
                
            file_path = os.path.join(date_path, file_name)
            summary = summarize_article(model, file_path)
            
            if summary:
                daily_summaries.append(summary)
                print(f"'{file_name}' 요약 완료")

        # 6. daily_summaries를 파일로 저장
        if daily_summaries:
            # SUMMARIZED_DATA_DIR 폴더가 없으면 생성
            os.makedirs(SUMMARIZED_DATA_DIR, exist_ok=True)
            
            # date_path에서 yyyymmdd 추출 (예: "data/20251025" -> "20251025")
            date_str = os.path.basename(date_path)
            
            # 파일명 생성: yyyymmdd.sum
            output_file = os.path.join(SUMMARIZED_DATA_DIR, f"{date_str}.sum")
            
            # 파일에 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                for summary in daily_summaries:
                    f.write(summary)
                    f.write('\n\n')  # 각 요약 뒤에 한 줄 띄기
            
            print(f"{date_folder}의 요약이 {output_file}에 저장되었습니다. (총 {len(daily_summaries)}개)")
        else:
            print(f"{date_folder} 폴더에서 요약할 기사를 찾을 수 없습니다.")

        # 7. 해당 날짜의 요약들을 종합 (주석 처리된 부분)
        # if daily_summaries:
        #     final_summary = summarize_all_articles(daily_summaries)
            
        #     # 결과 저장
        #     if final_summary:
        #         os.makedirs(SUMMARIZED_DATA_DIR, exist_ok=True)
        #         output_file = os.path.join(SUMMARIZED_DATA_DIR, f"{date_folder}.txt")
                
        #         with open(output_file, 'w', encoding='utf-8') as f:
        #             f.write(final_summary)
                
        #         print(f"{date_folder} 날짜의 종합 요약이 {output_file}에 저장되었습니다.")
        # else:
        #     print(f"{date_folder} 폴더에서 요약할 기사를 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
