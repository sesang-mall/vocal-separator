# 📁 프로젝트 구조

```
vocal-separator/
├── main.py                      # 메인 GUI 애플리케이션
├── audio_processor.py           # 음성 처리 로직
├── requirements.txt             # Python 의존성
├── setup.bat                    # Windows 자동 설치 스크립트
├── README.md                    # 상세 설명서
├── QUICK_START.md               # 빠른 시작 가이드
└── output/                      # 분리된 음악 저장 폴더 (자동 생성)
```

## 📄 파일별 설명

### main.py
- **PySimpleGUI** 기반 사용자 인터페이스
- 로컬 파일/유튜브 URL 입력 처리
- 실시간 로그 표시
- 멀티스레딩으로 UI 응답성 유지

### audio_processor.py
- **AudioProcessor** 클래스: 모든 음성 처리 작업 담당
- `download_from_youtube()`: 유튜브 음원 다운로드
- `separate_with_spleeter()`: 빠른 분리 (보컬 + 악기)
- `separate_with_demucs()`: 고품질 분리 (4가지 요소)
- `get_audio_info()`: 오디오 파일 정보 조회

### requirements.txt
필수 라이브러리:
- **PySimpleGUI**: GUI
- **librosa**: 오디오 처리
- **soundfile**: 음성 파일 입출력
- **torch**: 딥러닝 프레임워크
- **torchaudio**: 음성 처리
- **spleeter**: 빠른 음성 분리
- **demucs**: 고품질 음성 분리
- **yt-dlp**: 유튜브 다운로드

### setup.bat
- Windows 자동 설치 스크립트
- Python/FFmpeg 설치 여부 확인
- 모든 의존성 자동 설치

## 🔄 프로그램 실행 흐름

```
1. main.py 실행
    ↓
2. PySimpleGUI 윈도우 생성
    ↓
3. 사용자 입력 대기
    ├─ 로컬 파일 선택 OR
    └─ 유튜브 URL 입력
    ↓
4. 분리 방식 선택
    ├─ Spleeter (빠름)
    └─ Demucs (고품질)
    ↓
5. "분리 시작" 클릭 → 별도 스레드에서 처리
    ↓
6. AudioProcessor 실행
    ├─ YouTube 다운로드 (필요시)
    ├─ 오디오 정보 분석
    └─ Spleeter 또는 Demucs 실행
    ↓
7. 결과 저장 (output 폴더)
    ↓
8. 결과 폴더 자동 열기 (옵션)
```

## 🎯 커스터마이징 포인트

### 분리 방식 추가
`audio_processor.py`의 `AudioProcessor` 클래스에 메서드 추가:
```python
def separate_with_new_method(self, audio_path):
    # 새로운 음성 분리 방식 구현
    pass
```

### UI 개선
`main.py`의 `create_layout()` 함수에서 PySimpleGUI 요소 수정

### 출력 형식 변경
`audio_processor.py`에서 `soundfile.write()` 호출 시 형식 지정:
```python
sf.write(output_path, audio, sr, subtype='PCM_16')  # MP3나 다른 형식
```

## ⚙️ 환경 변수 (선택사항)

```bash
# GPU 가속 활성화 (NVIDIA CUDA)
# main.py 실행 전에 설정
set CUDA_VISIBLE_DEVICES=0

# 로깅 레벨 설정
set DEMUCS_LOG_LEVEL=DEBUG
```

## 🧪 테스트 방법

1. **GUI 테스트**
   ```bash
   python main.py
   ```

2. **개별 함수 테스트**
   ```python
   from audio_processor import AudioProcessor
   
   processor = AudioProcessor()
   processor.separate_with_spleeter('test.mp3')
   ```

3. **유튜브 다운로드 테스트**
   ```python
   url = "https://www.youtube.com/watch?v=..."
   processor.download_from_youtube(url)
   ```
