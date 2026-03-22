import time
from data_manager import reset_and_archive

if __name__ == "__main__":
    print("Executing Midnight Reset & PDF Archive via GitHub Actions...")
    
    # GHA cron이 정확히 정각보다 몇 초 일찍 도는 것을 대비해 10초 딜레이
    time.sleep(10)
    
    # 24시간 데이터 PDF 변환 및 파일 저장, 그리고 JSON 초기화
    reset_and_archive()
    
    print("Archive complete! The repository should now commit the new PDF and reset JSON.")
