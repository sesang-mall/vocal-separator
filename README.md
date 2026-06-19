# 🎵 보컬 & 음악 분리 앱

MP3 파일이나 유튜브 URL을 입력하면 보컬과 음악을 자동으로 분리하는 데스크톱 애플리케이션입니다.

## ✨ 주요 기능

- **두 가지 분리 방식**
  - **Spleeter** (빠른 처리): 2-5분 내에 보컬과 악기 분리
  - **Demucs** (고품질): 더 정확한 분리 (보컬, 드럼, 베이스, 기타) 10-20분

- **다양한 입력 방식**
  - 로컬 MP3 파일 직접 선택
  - 유튜브 URL에서 자동 다운로드

- **편의 기능**
  - 진행 상황 실시간 표시
  - 처리 완료 후 자동으로 결과 폴더 열기
  - 원본 파일 자동 삭제 옵션

## 🚀 설치 방법

### 1. Python 설치
Python 3.8 이상이 필요합니다.

### 2. 의존성 설치

```bash
cd vocal-separator
pip install -r requirements.txt
```

### 3. FFmpeg 설치 (필수)

**Windows:**
```bash
# chocolatey 사용
choco install ffmpeg

# 또는 winget 사용
winget install FFmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

## 📖 사용 방법

```bash
python main.py
```

1. **입력 선택**
   - 로컬 파일: "파일 선택" 버튼으로 MP3 파일 선택
   - 유튜브: URL 라디오 버튼 선택 후 URL 입력

2. **분리 방식 선택**
   - **Spleeter**: 빠른 처리가 필요할 때 (실시간 사용, 배경음악 제거 등)
   - **Demucs**: 더 정확한 분리가 필요할 때 (음악 제작, 리믹싱 등)

3. **옵션 설정**
   - 결과 폴더 자동 열기
   - 처리 완료 후 원본 파일 자동 삭제

4. **분리 시작**
   - "분리 시작" 버튼 클릭
   - 진행 상황을 콘솔에서 확인

## 📂 출력 파일

### Spleeter 결과
```
output/spleeter_output/[파일명]/
├── vocals.wav      # 보컬
└── accompaniment.wav  # 악기
```

### Demucs 결과
```
output/[모델명]/[파일명]/
├── vocals.wav      # 보컬
├── drums.wav       # 드럼
├── bass.wav        # 베이스
├── other.wav       # 기타
└── mixture.wav     # 원본
```

## ⚙️ 시스템 요구사항

- **CPU**: Intel i5 이상 권장
- **RAM**: 최소 8GB
- **저장소**: 처리 중인 파일 크기의 10배 이상 여유 필요
- **GPU** (선택): NVIDIA CUDA 지원 GPU가 있으면 처리 속도 5-10배 향상

## 🔧 문제 해결

### "spleeter 또는 demucs 명령을 찾을 수 없습니다"
```bash
# 다시 설치
pip uninstall spleeter demucs
pip install spleeter demucs
```

### "FFmpeg를 찾을 수 없습니다"
- FFmpeg가 설치되지 않았습니다. 위의 설치 방법을 따르세요

### "유튜브 다운로드 실패"
- yt-dlp를 최신 버전으로 업데이트하세요:
```bash
pip install --upgrade yt-dlp
```

### 처리 속도가 매우 느림
- CPU 처리이므로 정상입니다
- GPU 가속을 위해 CUDA를 설치하면 더 빨라집니다
- 더 짧은 곡부터 테스트해보세요

## 📝 라이선스

오픈소스 라이선스 (MIT)

## 🙏 감사의 말

- [Spleeter](https://github.com/deezer/spleeter) - Deezer
- [Demucs](https://github.com/facebookresearch/demucs) - Meta/Facebook
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
