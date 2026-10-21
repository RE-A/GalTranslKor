import re
import requests
import time
import os
import math
import wave
import struct
from GalTransl import LOGGER
from GalTransl.CSentense import CSentense
from GalTransl.GTPlugin import GTextPlugin

try:
    import playsound3
except ImportError:
    LOGGER.warning("의존성 패키지 playsound3가 없습니다. 의존성을 업데이트하지 않으면 소리 알림을 재생할 수 없습니다.")

class ServerChanNotifier(GTextPlugin):
    SERVERCHAN_API_URL = 'https://sctapi.ftqq.com/{}.send'
    TELEGRAM_API_URL = '{}/bot{}/sendMessage'

    def gtp_init(self, plugin_conf: dict, project_conf: dict):
        self.start_time = time.time()
        self.pname = plugin_conf["Core"].get("Name", "완료 알림")
        settings = plugin_conf["Settings"]
        self.push_channels = settings.get("推送渠道", [])
        self.tg_bot_url = settings.get("Telegram_Bot_API_URL", "https://api.telegram.org").rstrip('/')
        self.tg_bot_token = settings.get("Telegram_Bot_Token", "")
        self.tg_chat_id = settings.get("Telegram_Bot_ChatID", "")
        self.serverchan_sendkey = settings.get("ServerChan_SendKey", "")
        self.project_dir = project_conf["project_dir"]
        self.gt_input_dir = os.path.join(self.project_dir, "gt_input")
        self.gt_output_dir = os.path.join(self.project_dir, "gt_output")
        self.project_name = os.path.basename(self.project_dir)
        
        # 声音通知设置
        self.enable_sound = settings.get("启用声音通知", False)
        self.use_custom_audio = settings.get("使用自定义音频", False)
        self.use_openai_tts = settings.get("使用OpenAI TTS", False)
        self.openai_api_key = settings.get("OpenAI_API_Key", "")
        self.openai_api_base_url = settings.get("OpenAI_API_Base_URL", "https://api.openai.com/v1")
        self.openai_tts_voice = settings.get("OpenAI_TTS_Voice", "alloy")

        # 获取声音文件路径
        self.plugin_dir = os.path.abspath(os.path.dirname(__file__))
        self.success_audio_path = os.path.join(self.plugin_dir, "default_sound", "success.wav")
        self.fail_audio_path = os.path.join(self.plugin_dir, "default_sound", "fail.wav")

        if self.use_custom_audio:
            custom_success_path = settings.get("成功音频路径", "")
            custom_fail_path = settings.get("失败音频路径", "")
            if custom_success_path:
                self.success_audio_path = os.path.join(self.plugin_dir, custom_success_path)
            if custom_fail_path:
                self.fail_audio_path = os.path.join(self.plugin_dir, custom_fail_path)

        self._validate_config()

    def _validate_config(self):
        if not self.push_channels:
            LOGGER.warning(f"[{self.pname}] 알림 채널이 없어 플러그인이 알림을 보내지 않습니다.")
        else:
            LOGGER.debug(f"[{self.pname}] 플러그인 초기화 성공. 알림 채널: {', '.join(self.push_channels)}")
        
        if self.enable_sound:
            if self.use_custom_audio:
                if not os.path.exists(self.success_audio_path):
                    LOGGER.warning(f"[{self.pname}] 성공 오디오 파일이 없습니다: {self.success_audio_path}")
                if not os.path.exists(self.fail_audio_path):
                    LOGGER.warning(f"[{self.pname}] 실패 오디오 파일이 없습니다: {self.fail_audio_path}")
            elif self.use_openai_tts and not self.openai_api_key:
                LOGGER.warning(f"[{self.pname}] OpenAI API Key가 없어 OpenAI TTS를 쓸 수 없습니다")

    def before_src_processed(self, tran: CSentense) -> CSentense:
        return tran

    def after_src_processed(self, tran: CSentense) -> CSentense:
        return tran

    def before_dst_processed(self, tran: CSentense) -> CSentense:
        return tran

    def after_dst_processed(self, tran: CSentense) -> CSentense:
        return tran

    def gtp_final(self):
        end_time = time.time()
        total_time = end_time - self.start_time
        total_time_format = time.strftime("%H시간 %M분 %S초", time.gmtime(total_time))

        input_files = set(os.listdir(self.gt_input_dir))
        output_files = set(os.listdir(self.gt_output_dir))
        untranslated_files = input_files - output_files

        title, content = self._generate_notification_content(total_time_format, untranslated_files)

        for channel in self.push_channels:
            if channel == "ServerChan":
                if self.serverchan_sendkey:
                    self.send_serverchan_notification(title, content)
                else:
                    LOGGER.warning(f"[{self.pname}] ServerChan SendKey가 없어 ServerChan 알림을 보낼 수 없습니다.")
            elif channel == "Telegram Bot":
                if self.tg_bot_token and self.tg_chat_id:
                    self.send_telegram_notification(title, content)
                else:
                    LOGGER.warning(f"[{self.pname}] Telegram Bot Token이나 ChatID가 없어 Telegram 알림을 보낼 수 없습니다.")
            else:
                LOGGER.warning(f"[{self.pname}] 알 수 없는 알림 채널: {channel}")

        if not self.push_channels:
            LOGGER.warning(f"[{self.pname}] 알림 채널이 없어 알림 보내기를 건너뜁니다.")

        # 播放声音通知
        if self.enable_sound:
            self.play_notification_sound(title, content)

    def _generate_notification_content(self, total_time: str, untranslated_files: set) -> tuple:
        if not untranslated_files:
            title = f"[GalTransl] {self.project_name} 번역 완료"
            content = f"모든 파일 번역을 마쳤습니다. 총 소요 시간: {total_time}"
        else:
            title = f"[GalTransl] {self.project_name} 일부 파일 번역 완료"
            content = f"다음 파일은 번역에 실패했습니다. 총 소요 시간: {total_time}\n"
            content += "\n".join(f" - {file}" for file in sorted(untranslated_files))
        return title, content

    def send_serverchan_notification(self, title, content):
        api_url = self.SERVERCHAN_API_URL.format(self.serverchan_sendkey)
        data = {
            'text': title,
            'desp': content
        }
        
        try:
            response = requests.post(api_url, data=data)
            response.raise_for_status()
            LOGGER.info(f"[{self.pname}] ServerChan 알림 전송 성공")
        except requests.RequestException as e:
            LOGGER.error(f"[{self.pname}] ServerChan 알림 전송 중 오류: {str(e)}")
            if hasattr(e, 'response'):
                LOGGER.error(f"응답 내용: {e.response.text}")

    def send_telegram_notification(self, title, content):
        api_url = self.TELEGRAM_API_URL.format(self.tg_bot_url, self.tg_bot_token)
        
        message = f"*{self._escape_markdown(title)}*\n\n{self._escape_markdown(content)}"
        params = {
            "chat_id": self.tg_chat_id,
            "text": message,
            "parse_mode": "MarkdownV2"
        }
        
        try:
            response = requests.post(api_url, params=params)
            response.raise_for_status()
            LOGGER.info(f"[{self.pname}] Telegram Bot 알림 전송 성공")
        except requests.RequestException as e:
            LOGGER.error(f"[{self.pname}] Telegram Bot 알림 전송 중 오류: {str(e)}")
            if hasattr(e, 'response'):
                LOGGER.error(f"응답 내용: {e.response.text}")

    def play_notification_sound(self, title, content):
        is_success = "모든 파일 번역을 마쳤습니다" in content
        audio_path = self.success_audio_path if is_success else self.fail_audio_path

        if self.use_openai_tts:
            self.play_openai_tts(title, content)
        elif self.use_custom_audio or not self.use_openai_tts:
            if os.path.exists(audio_path):
                self.play_audio(audio_path)
            else:
                LOGGER.warning(f"[{self.pname}] 오디오 파일이 없습니다: {audio_path}")
                LOGGER.warning(f"[{self.pname}] beep 소리 재생")
                frequency = 440  # 设置频率为 440 Hz
                duration = 1000  # 设置持续时间为 1000 毫秒
                self.play_beep(frequency, duration)

    def play_openai_tts(self, title, content):
        if not self.openai_api_key:
            LOGGER.warning(f"[{self.pname}] OpenAI API Key가 없어 OpenAI TTS를 쓸 수 없습니다")
            return

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }

        full_message = f"{title}. {content}"
        data = {
            "model": "tts-1",
            "input": full_message,
            "voice": self.openai_tts_voice,
            "response_format": "mp3"  # 改为 mp3 格式
        }

        try:
            response = requests.post(f"{self.openai_api_base_url}/audio/speech", headers=headers, json=data)
            response.raise_for_status()
            
            mp3_file = os.path.join(self.project_dir, "openai_tts.mp3")
            with open(mp3_file, "wb") as f:
                f.write(response.content)
            
            LOGGER.debug(f"[{self.pname}] OpenAI TTS 오디오 파일 저장: {mp3_file}")
            
            self.play_audio(mp3_file)

            # 成功播放音频后删除临时文件
            os.remove(mp3_file)
            LOGGER.debug(f"[{self.pname}] OpenAI TTS 오디오 파일 삭제: {mp3_file}")
            
        except requests.RequestException as e:
            LOGGER.error(f"[{self.pname}] OpenAI TTS 요청 실패: {str(e)}")
        except Exception as e:
            LOGGER.error(f"[{self.pname}] 오디오 처리 또는 재생 중 오류: {str(e)}")

    def play_audio(self, audio_file):
        try:
            playsound3.playsound(audio_file)
            LOGGER.debug(f"[{self.pname}] 오디오 파일 재생 완료")
        except Exception as e:
            LOGGER.error(f"[{self.pname}] 오디오 파일 재생 중 오류: {str(e)}")

    def play_beep(self, frequency, duration):
        # 采样参数
        sample_rate = 44100
        num_samples = int(sample_rate * duration / 1000)

        # 生成正弦波
        samples = [int(32767 * math.sin(2 * math.pi * frequency * t / sample_rate)) for t in range(num_samples)]

        # 创建 WAV 文件
        temp_file = "temp_beep.wav"
        with wave.open(temp_file, "w") as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 2 字节采样
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(struct.pack('{}h'.format(len(samples)), *samples))

        # 播放音频
        playsound3.playsound(temp_file, block=True)  # 改为阻塞模式,确保播放完成

        # 删除临时文件
        os.remove(temp_file)

    @staticmethod
    def _escape_markdown(text):
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)