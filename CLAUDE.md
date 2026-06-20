# CLAUDE.md — Vocal Separator 프로젝트 컨텍스트

## 프로젝트 개요

MP3 파일 또는 유튜브 URL을 입력받아 **보컬 / 드럼 / 베이스 / 기타**를 분리하는 Windows 데스크톱 앱.
선택적으로 분리된 트랙을 **MIDI 파일로 변환**하는 기능도 포함.

---

## 기술 스택

| 역할 | 라이브러리 |
|------|-----------|
| GUI | CustomTkinter 5.x + tkinterdnd2 |
| 음원 분리 | Demucs 4.x (Facebook Research) |
| MIDI 변환 | basic-pitch (Spotify) |
| 유튜브 다운로드 | yt-dlp |
| 오디오 분석 | librosa |

---

## 파일 구조

```
vocal-separator/
├── main.py              # GUI 전체 (App 클래스)
├── audio_processor.py   # 핵심 처리 로직 (AudioProcessor 클래스)
├── requirements.txt
└── setup.bat            # Windows 최초 설치 스크립트
```

---

## 핵심 설계 결정

### Spleeter 대신 Demucs 단독 사용
- Spleeter는 Python 3.11에서 의존성 충돌이 심해 제거
- Demucs만으로 두 가지 모드 제공
  - **fast**: `htdemucs` (5–10분, 기본 품질)
  - **quality**: `htdemucs_ft` (15–30분, Fine-tuned 고품질)
- 두 모드 모두 4 스템 분리: `vocals / drums / bass / other`

### MIDI 변환 대상
- `vocals.wav`, `bass.wav`, `other.wav` → `.mid` 변환
- `drums.wav`는 음정이 없어 MIDI 변환에서 제외
- basic-pitch (Spotify)는 멜로디 악기에 최적화

### tqdm 진행률 파싱
Demucs는 tqdm을 stderr로 출력하며 `\r`로 줄을 덮어씀.
`text=True` + `readline()`으로는 `\r`을 잡을 수 없어 **binary 청크 읽기 + `re.split(b'[\r\n]')`** 방식으로 처리.

```python
# audio_processor.py — separate() 내부
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
buf = b''
while True:
    chunk = proc.stdout.read(256)
    ...
    parts = re.split(b'[\r\n]', buf)
```

tqdm 라인 파싱 정규식 (main.py):
```python
_TQDM_RE = re.compile(r'(\d+)%\|.*?\|\s*\S+\s*\[[\d:]+<([\d:]+)')
```

### 드래그 앤 드롭 파싱 — `tk.splitlist()` 사용
tkinterdnd2의 `event.data`는 TCL 리스트 형식.
공백 없는 파일과 공백 있는 파일이 섞이면 raw가 `{`로 시작하지 않아
단순 `split()` 또는 regex만으로는 경로가 잘림.

**해결책: `self.tk.splitlist(event.data)`** — tkinter 내장 TCL 파서 사용.

```python
# main.py — _on_drop()
try:
    paths = self.tk.splitlist(event.data)
except Exception:
    raw = event.data.strip()
    paths = re.findall(r'\{([^}]+)\}', raw) if '{' in raw else raw.split()
```

### CTk + tkinterdnd2 결합
`ctk.CTk`와 `TkinterDnD.DnDWrapper`를 다중 상속으로 결합.

```python
class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
```

### 대기열 처리
- `QueueItem` 데이터클래스로 상태 관리 (`waiting / processing / done / error`)
- 처리는 단일 백그라운드 스레드에서 순차 실행
- UI 업데이트는 반드시 `self.after(0, ...)` 로 메인 스레드에 위임
- 처리 중인 항목은 개별 제거 불가 (UX 보호)

---

## 진행률 UI 구조

```
[전체 진행 바]  2 / 5  · 처리 중 · 곡제목.mp3   ← overall_bar (초록)
[현재 파일 바]  ████████░░  45%  남은 시간 01:23  ← progress (파란)
```

- 모델 로딩 중: indeterminate (흐르는 애니메이션)
- tqdm 출력 감지 시: determinate (실제 퍼센트)로 자동 전환

---

## 결과 파일 구조

```
output/
└── htdemucs_ft/        ← 모델명
    └── 곡제목/          ← 입력 파일명
        ├── vocals.wav   → vocals.mid  (MIDI 변환 시)
        ├── drums.wav
        ├── bass.wav     → bass.mid
        └── other.wav    → other.mid
```

---

## 설치 및 실행

```bat
# 최초 설치
setup.bat

# 실행
python main.py
```

**사전 요구사항**
- Python 3.11+
- FFmpeg (PATH 등록 필요)
- 첫 실행 시 Demucs 모델 자동 다운로드 (~300MB)

---

## 알려진 제약

- `basic-pitch`가 설치한 `protobuf 4.25.9`가 기존 `audiocraft` 등과 버전 충돌 경고를 내지만 이 앱 동작에는 무관
- GPU 없이 CPU로 실행 시 처리 시간이 2–3배 느려짐
- 유튜브 다운로드는 `yt-dlp` 최신 버전 유지 필요 (YouTube API 변경 대응)

---

## 향후 확장 시 참고

### AI 커버곡 파이프라인 연계
이 앱으로 분리한 `vocals.wav`는 **RVC(Retrieval-based Voice Conversion)** 학습 데이터로 바로 사용 가능.

- 학습 데이터 권장: 동일 가수 보컬 10–30분 이상, `htdemucs_ft` 모드로 분리
- 권장 도구: **Applio** (RVC GUI 래퍼, 완성도 높음)
- 이 앱과 Applio는 **분리 운영** 권장
  - RVC 의존성(CUDA, 대형 모델)이 무거워 통합 시 앱 전체가 비대해짐
  - 연결 방법: 결과 폴더를 Applio 입력으로 지정하는 방식으로 충분
- 상업적 배포 시 실제 가수 음성 학습은 저작권·초상권 이슈 주의
