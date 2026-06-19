import re
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
from pathlib import Path
import threading
import subprocess
from audio_processor import AudioProcessor

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

processor = AudioProcessor()

ACCENT    = "#4fc3f7"
SUCCESS   = "#2e7d32"
CARD_BG   = "#1e1e2e"
DROP_BG   = "#16213e"
DROP_HOVER= "#1a2a4a"
LOG_BG    = "#0d0d0d"
LOG_FG    = "#90ee90"
GRAY      = "#6b7280"
BORDER    = "#2a2a3e"
BORDER_HOVER = "#4fc3f7"


# CTk + tkinterdnd2 를 함께 사용하기 위한 결합
class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("Vocal Separator")
        self.geometry("800x720")
        self.minsize(700, 620)
        self.configure(fg_color="#13131f")

        self.audio_path: str | None = None
        self.busy = False

        self._build()

    # ──────────────────────────────────────────────
    # Layout
    # ──────────────────────────────────────────────
    def _build(self):
        self._header()
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(10, 0))
        self._input_card(scroll)
        self._settings_row(scroll)
        self._start_button(scroll)
        self._progress_bar(scroll)
        self._log_box(scroll)

    def _header(self):
        hdr = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="  🎵  Vocal Separator",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ACCENT,
        ).pack(side="left", padx=16)
        ctk.CTkLabel(
            hdr, text="AI 기반 보컬 & 음원 분리 도구",
            font=ctk.CTkFont(size=11), text_color=GRAY,
        ).pack(side="left")

    def _input_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12)
        card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            card, text="입력 소스",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 8))

        self.seg = ctk.CTkSegmentedButton(
            card,
            values=["  로컬 파일  ", "  유튜브 URL  "],
            command=self._on_tab,
            selected_color="#1565c0",
            selected_hover_color="#1976d2",
            font=ctk.CTkFont(size=12),
        )
        self.seg.set("  로컬 파일  ")
        self.seg.pack(anchor="w", padx=16)

        # ── 파일 패널 ──
        self.file_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.file_frame.pack(fill="x", padx=16, pady=(10, 14))

        # 드롭 존
        self.drop_zone = ctk.CTkFrame(
            self.file_frame,
            height=90,
            fg_color=DROP_BG,
            border_color=BORDER,
            border_width=2,
            corner_radius=10,
        )
        self.drop_zone.pack(fill="x", pady=(0, 8))
        self.drop_zone.pack_propagate(False)

        self.drop_icon = ctk.CTkLabel(
            self.drop_zone,
            text="📂",
            font=ctk.CTkFont(size=26),
        )
        self.drop_icon.pack(pady=(12, 2))

        self.drop_label = ctk.CTkLabel(
            self.drop_zone,
            text="여기에 파일을 드래그하세요",
            font=ctk.CTkFont(size=12),
            text_color=GRAY,
        )
        self.drop_label.pack()

        # 드롭 이벤트 등록 (zone + 내부 레이블 모두)
        for widget in (self.drop_zone, self.drop_icon, self.drop_label):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>",       self._on_drop)
            widget.dnd_bind("<<DragEnter>>",  self._on_drag_enter)
            widget.dnd_bind("<<DragLeave>>",  self._on_drag_leave)

        # 파일 경로 표시 + 버튼
        bottom = ctk.CTkFrame(self.file_frame, fg_color="transparent")
        bottom.pack(fill="x")

        self.file_entry = ctk.CTkEntry(
            bottom,
            placeholder_text="선택된 파일 없음",
            height=36, state="disabled",
            border_color=BORDER,
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            bottom, text="파일 선택", width=100, height=36,
            fg_color="#1565c0", hover_color="#1976d2",
            command=self._browse,
        ).pack(side="left")

        # ── URL 패널 ──
        self.url_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=38, border_color=BORDER,
        )
        self.url_entry.pack(fill="x", pady=(10, 14))

    def _settings_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)
        self._model_card(row)
        self._options_card(row)

    def _model_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ctk.CTkLabel(
            card, text="분리 방식",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 10))

        self.model_var = tk.StringVar(value="fast")
        for val, icon, label, desc in [
            ("fast",    "⚡", "빠른 처리", "htdemucs  ·  5–10분"),
            ("quality", "⭐", "고품질",   "htdemucs_ft  ·  15–30분"),
        ]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkRadioButton(
                row, text=f"{icon}  {label}",
                variable=self.model_var, value=val,
                font=ctk.CTkFont(size=12),
                radiobutton_width=16, radiobutton_height=16,
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=desc, text_color=GRAY,
                font=ctk.CTkFont(size=10),
            ).pack(side="left", padx=(10, 0))
        ctk.CTkFrame(card, height=14, fg_color="transparent").pack()

    def _options_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12)
        card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ctk.CTkLabel(
            card, text="옵션",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 10))

        self.open_var = tk.BooleanVar(value=True)
        self.midi_var = tk.BooleanVar(value=False)
        for var, text in [
            (self.open_var, "완료 후 결과 폴더 열기"),
            (self.midi_var, "MIDI 자동 변환\n(vocals / bass / other)"),
        ]:
            ctk.CTkCheckBox(
                card, text=text, variable=var,
                font=ctk.CTkFont(size=12),
                checkbox_width=18, checkbox_height=18,
            ).pack(anchor="w", padx=16, pady=4)
        ctk.CTkFrame(card, height=10, fg_color="transparent").pack()

    def _start_button(self, parent):
        self.start_btn = ctk.CTkButton(
            parent, text="▶   분리 시작", height=52,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=SUCCESS, hover_color="#388e3c",
            corner_radius=10, command=self._on_start,
        )
        self.start_btn.pack(fill="x", pady=(0, 10))

    def _progress_bar(self, parent):
        self.progress = ctk.CTkProgressBar(
            parent, height=8, corner_radius=4,
            fg_color=CARD_BG, progress_color=ACCENT,
        )
        self.progress.pack(fill="x", pady=(0, 4))
        self.progress.set(0)

        stat_row = ctk.CTkFrame(parent, fg_color="transparent")
        stat_row.pack(fill="x", pady=(0, 6))

        self.pct_label = ctk.CTkLabel(
            stat_row, text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=ACCENT,
        )
        self.pct_label.pack(side="left")

        self.eta_label = ctk.CTkLabel(
            stat_row, text="",
            font=ctk.CTkFont(size=12),
            text_color=GRAY,
        )
        self.eta_label.pack(side="right")

    def _log_box(self, parent):
        ctk.CTkLabel(
            parent, text="처리 로그",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=GRAY,
        ).pack(anchor="w")
        self.log = ctk.CTkTextbox(
            parent, height=200,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=LOG_BG, text_color=LOG_FG,
            border_color=BORDER, border_width=1,
            corner_radius=8,
        )
        self.log.pack(fill="both", expand=True, pady=(4, 20))

    # ──────────────────────────────────────────────
    # 드래그 앤 드롭 이벤트
    # ──────────────────────────────────────────────
    def _on_drag_enter(self, event):
        self.drop_zone.configure(fg_color=DROP_HOVER, border_color=BORDER_HOVER)
        self.drop_label.configure(text="놓으면 파일이 추가됩니다", text_color=ACCENT)

    def _on_drag_leave(self, event):
        self._reset_drop_zone()

    def _on_drop(self, event):
        self._reset_drop_zone()
        # Windows는 여러 파일이면 중괄호로 묶임 — 첫 번째 파일만 사용
        raw = event.data.strip()
        path = raw.strip("{}").split("} {")[0] if raw.startswith("{") else raw.split()[0]
        self._set_file(path)

    def _reset_drop_zone(self):
        self.drop_zone.configure(fg_color=DROP_BG, border_color=BORDER)
        self.drop_label.configure(text="여기에 파일을 드래그하세요", text_color=GRAY)

    # ──────────────────────────────────────────────
    # 파일 선택 공통
    # ──────────────────────────────────────────────
    def _browse(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("오디오 파일", "*.mp3 *.wav *.flac *.m4a"),
                ("전체 파일", "*.*"),
            ]
        )
        if path:
            self._set_file(path)

    def _set_file(self, path: str):
        self.audio_path = path
        name = Path(path).name
        self.file_entry.configure(state="normal")
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, path)
        self.file_entry.configure(state="disabled")
        self.drop_icon.configure(text="✅")
        self.drop_label.configure(text=name, text_color="white")

    def _on_tab(self, value):
        if "파일" in value:
            self.url_frame.pack_forget()
            self.file_frame.pack(fill="x", padx=16, pady=(10, 14))
        else:
            self.file_frame.pack_forget()
            self.url_frame.pack(fill="x", padx=16)

    # ──────────────────────────────────────────────
    # 진행률 파싱 & 업데이트
    # ──────────────────────────────────────────────
    _TQDM_RE = re.compile(r'(\d+)%\|.*?\|\s*\S+\s*\[[\d:]+<([\d:]+)')

    def _parse_tqdm(self, line: str):
        """tqdm 줄에서 (pct, remaining) 반환. 아니면 (None, None)."""
        m = self._TQDM_RE.search(line)
        if m:
            return int(m.group(1)), m.group(2)
        return None, None

    def _update_progress_ui(self, pct: int, remaining: str | None):
        """메인 스레드에서 진행바·라벨 업데이트."""
        self.progress.configure(mode="determinate")
        self.progress.set(pct / 100)
        self.pct_label.configure(text=f"{pct}%")
        if remaining and remaining != "?":
            self.eta_label.configure(text=f"남은 시간  {remaining}")
        elif pct == 100:
            self.eta_label.configure(text="완료!")

    # ──────────────────────────────────────────────
    # 로그
    # ──────────────────────────────────────────────
    def _emit(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    # ──────────────────────────────────────────────
    # 처리 파이프라인
    # ──────────────────────────────────────────────
    def _on_start(self):
        if self.busy:
            return

        if "파일" in self.seg.get():
            if not self.audio_path or not Path(self.audio_path).exists():
                self._emit("❌ 파일을 선택하거나 드래그해주세요.")
                return
            audio_path = self.audio_path
        else:
            url = self.url_entry.get().strip()
            if not url:
                self._emit("❌ URL을 입력해주세요.")
                return
            self._emit("[다운로드] 유튜브에서 다운로드 중...")
            try:
                audio_path = processor.download_from_youtube(url)
                self._emit(f"[완료] {Path(audio_path).name}")
            except Exception as e:
                self._emit(f"❌ 다운로드 실패: {e}")
                return

        mode      = self.model_var.get()
        auto_midi = self.midi_var.get()
        open_dir  = self.open_var.get()

        self.busy = True
        self.start_btn.configure(state="disabled", text="⏳  처리 중...")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.pct_label.configure(text="준비 중...")
        self.eta_label.configure(text="")

        threading.Thread(
            target=self._pipeline,
            args=(audio_path, mode, auto_midi, open_dir),
            daemon=True,
        ).start()

    def _pipeline(self, audio_path, mode, auto_midi, open_dir):
        try:
            self._emit(f"\n{'─'*50}")
            self._emit(f"[정보] {Path(audio_path).name}")
            info = processor.get_audio_info(audio_path)
            self._emit(f"[정보] 길이={info['duration']}  SR={info['sample_rate']}Hz  채널={info['channels']}")

            model_name = "htdemucs" if mode == "fast" else "htdemucs_ft"
            self._emit(f"[분리] 모델: {model_name}")

            def on_demucs_line(line: str):
                pct, remaining = self._parse_tqdm(line)
                if pct is not None:
                    self.after(0, lambda p=pct, r=remaining: self._update_progress_ui(p, r))
                else:
                    self._emit(f"  {line}")

            result_dir = processor.separate(
                audio_path, mode=mode,
                progress_callback=on_demucs_line,
            )
            self._emit("[분리 완료] ✅")
            self._emit(f"  → {result_dir}")

            if auto_midi:
                self._emit("[MIDI] 변환 시작...")
                midi_files = processor.convert_to_midi(
                    result_dir,
                    progress_callback=lambda m: self._emit(f"  {m}"),
                )
                self._emit(f"[MIDI 완료] ✅  {len(midi_files)}개 파일 생성")

            self._emit(f"{'─'*50}\n")

            if open_dir:
                subprocess.Popen(f'explorer "{result_dir}"')

        except Exception as e:
            self._emit(f"[오류] ❌ {e}")

        finally:
            self.busy = False
            self.after(0, self._reset_ui)

    def _reset_ui(self):
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(1)
        self.pct_label.configure(text="100%")
        self.eta_label.configure(text="완료!")
        self.start_btn.configure(state="normal", text="▶   분리 시작")


if __name__ == "__main__":
    App().mainloop()
