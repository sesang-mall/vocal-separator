import re
import subprocess
from pathlib import Path
import yt_dlp
import librosa


class AudioProcessor:
    MODELS = {
        'fast': 'htdemucs',
        'quality': 'htdemucs_ft',
    }

    # 드럼은 음정이 없어 MIDI 변환 의미 없음
    MIDI_STEMS = ['vocals', 'bass', 'other']

    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def download_from_youtube(self, url):
        """유튜브에서 음원 다운로드 후 경로 반환"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'audio')
            return str(self.output_dir / f"{title}.mp3")

    def separate(self, audio_path, mode='fast', progress_callback=None):
        """
        Demucs로 음원 분리.
        mode='fast'    → htdemucs  (빠름)
        mode='quality' → htdemucs_ft (고품질)
        분리 결과 폴더 경로 반환.
        """
        model = self.MODELS[mode]
        cmd = [
            'python', '-m', 'demucs',
            '-n', model,
            '-o', str(self.output_dir),
            audio_path,
        ]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,  # unbuffered — tqdm \r 즉시 전달
        )
        buf = b''
        while True:
            chunk = proc.stdout.read(256)
            if not chunk:
                break
            buf += chunk
            # \r 과 \n 모두 구분자로 분리 (tqdm은 \r로 같은 줄을 덮어씀)
            parts = re.split(b'[\r\n]', buf)
            for part in parts[:-1]:
                line = part.decode('utf-8', errors='replace').strip()
                if line and progress_callback:
                    progress_callback(line)
            buf = parts[-1]
        if buf:
            line = buf.decode('utf-8', errors='replace').strip()
            if line and progress_callback:
                progress_callback(line)
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"Demucs 종료 코드: {proc.returncode}")

        stem_name = Path(audio_path).stem
        return self.output_dir / model / stem_name

    def convert_to_midi(self, stem_dir, progress_callback=None):
        """
        분리된 트랙(vocals, bass, other)을 MIDI로 변환.
        basic-pitch 사용. 드럼은 음정 없으므로 건너뜀.
        생성된 .mid 파일 경로 목록 반환.
        """
        from basic_pitch.inference import predict
        from basic_pitch import ICASSP_2022_MODEL_PATH

        stem_dir = Path(stem_dir)
        midi_files = []

        for stem in self.MIDI_STEMS:
            wav_path = stem_dir / f"{stem}.wav"
            if not wav_path.exists():
                continue

            if progress_callback:
                progress_callback(f"MIDI 변환 중: {stem}.wav")

            _, midi_data, _ = predict(
                str(wav_path),
                ICASSP_2022_MODEL_PATH,
            )

            midi_path = stem_dir / f"{stem}.mid"
            midi_data.write(str(midi_path))
            midi_files.append(midi_path)

            if progress_callback:
                progress_callback(f"  → {stem}.mid 저장 완료")

        return midi_files

    def get_audio_info(self, audio_path):
        """오디오 파일 기본 정보 반환"""
        y, sr = librosa.load(audio_path, sr=None, mono=False)
        duration = librosa.get_duration(y=y, sr=sr)
        return {
            'duration': f"{int(duration // 60)}:{int(duration % 60):02d}",
            'sample_rate': sr,
            'channels': 1 if y.ndim == 1 else y.shape[0],
        }
