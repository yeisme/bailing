import json
import queue
import threading
from abc import ABC
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import argparse
import time

from bailing import recorder, player, asr, llm, tts, vad, memory, rag
from bailing.dialogue import Message, Dialogue
from bailing.utils import (
    read_config,
    is_segment,
)
# 添加RAG导入

logger = logging.getLogger(__name__)

# 由于deepseek工具调用不太准，经常会输出到content，所以显示指明参数
sys_prompt = """
# 角色定义
你是百聆，一个AI聊天机器人。你性格开朗、活泼，善于交流。你的回复应该简短、友好、口语化强一些，回复禁止出现表情符号。

#以下是历史对话摘要:
{memory}

# 文档知识库检索结果:
{rag_context}

# 回复要求
1. 你的回复应该简短、友好、口语化强一些，回复禁止出现表情符号。
2. 如果需要调用工具，先不要回答，调用工具后再回答，直接输出工具名和参数，输出格式```json\n{"function_name":"", "args":{}}```
3. 如果检索到相关文档内容，请优先基于文档内容回答，并可以提及信息来源。
4. 如果没有检索到相关内容，请基于你的知识正常回答。
"""


class Robot(ABC):
    def __init__(self, config_file, mcp_config=None):
        config = read_config(config_file)
        self.audio_queue = queue.Queue()

        self.recorder = recorder.create_instance(
            config["selected_module"]["Recorder"],
            config["Recorder"][config["selected_module"]["Recorder"]],
        )

        self.asr = asr.create_instance(
            config["selected_module"]["ASR"],
            config["ASR"][config["selected_module"]["ASR"]],
        )

        self.llm = llm.create_instance(
            config["selected_module"]["LLM"],
            config["LLM"][config["selected_module"]["LLM"]],
        )

        self.tts = tts.create_instance(
            config["selected_module"]["TTS"],
            config["TTS"][config["selected_module"]["TTS"]],
        )

        self.vad = vad.create_instance(
            config["selected_module"]["VAD"],
            config["VAD"][config["selected_module"]["VAD"]],
        )

        self.player = player.create_instance(
            config["selected_module"]["Player"],
            config["Player"][config["selected_module"]["Player"]],
        )

        # self.MCP = mcp.create_instance(
        #     config["selected_module"]["MCP"],
        #     config["MCP"][config["selected_module"]["MCP"]],
        # )

        self.memory = memory.Memory(config.get("Memory"))

        # 初始化RAG系统
        try:
            self.rag = rag.create_rag_instance(documents_dir="documents")
            logger.info("RAG系统初始化成功")
        except Exception as e:
            logger.warning(f"RAG系统初始化失败: {e}")
            self.rag = None

        # 初始化对话相关组件
        self.vad_queue = queue.Queue()
        self.dialogue = Dialogue(config["Memory"]["dialogue_history_path"])

        # 初始化系统提示词（延迟到需要时再设置）
        self._update_system_prompt()

        # 保证tts是顺序的
        self.tts_queue = queue.Queue()
        # 初始化线程池
        self.executor = ThreadPoolExecutor(max_workers=10)

        self.vad_start = True

        # 打断相关配置
        self.INTERRUPT = config["interrupt"]
        self.silence_time_ms = int((1000 / 1000) * (16000 / 512))  # ms

        # 线程锁
        self.chat_lock = False

        # 事件用于控制程序退出
        self.stop_event = threading.Event()

        self.callback = None

        self.speech = []

    def listen_dialogue(self, callback):
        self.callback = callback

    def _stream_vad(self):
        def vad_thread():
            while not self.stop_event.is_set():
                try:
                    data = self.audio_queue.get()
                    vad_statue = self.vad.is_vad(data)
                    self.vad_queue.put({"voice": data, "vad_statue": vad_statue})
                except Exception as e:
                    logger.error(f"VAD 处理出错: {e}")

        consumer_audio = threading.Thread(target=vad_thread, daemon=True)
        consumer_audio.start()

    def _tts_priority(self):
        def priority_thread():
            while not self.stop_event.is_set():
                try:
                    future = self.tts_queue.get()
                    try:
                        tts_file = future.result(timeout=5)
                    except TimeoutError:
                        logger.error("TTS 任务超时")
                        continue
                    except Exception as e:
                        logger.error(f"TTS 任务出错: {e}")
                        continue
                    if tts_file is None:
                        continue
                    self.player.play(tts_file)
                except Exception as e:
                    logger.error(f"tts_priority priority_thread: {e}")

        tts_priority = threading.Thread(target=priority_thread, daemon=True)
        tts_priority.start()

    def interrupt_playback(self):
        """中断当前的语音播放"""
        logger.info("Interrupting current playback.")
        self.player.stop()

    def shutdown(self):
        """关闭所有资源，确保程序安全退出"""
        logger.info("Shutting down Robot...")
        self.stop_event.set()
        self.executor.shutdown(wait=True)
        self.recorder.stop_recording()
        self.player.shutdown()
        logger.info("Shutdown complete.")

    def start_recording_and_vad(self):
        # 开始监听语音流
        self.recorder.start_recording(self.audio_queue)
        logger.info("Started recording.")
        # vad 实时识别
        self._stream_vad()
        # tts优先级队列
        self._tts_priority()

    def _update_system_prompt(self, rag_context=""):
        """更新系统提示词，包含RAG上下文"""
        memory_content = self.memory.get_memory()
        self.prompt = (
            sys_prompt.replace("{memory}", memory_content)
            .replace("{rag_context}", rag_context)
            .strip()
        )

        # 更新对话中的系统消息
        if (
            len(self.dialogue.dialogue) > 0
            and self.dialogue.dialogue[0].role == "system"
        ):
            self.dialogue.dialogue[0] = Message(role="system", content=self.prompt)
        else:
            self.dialogue.put(Message(role="system", content=self.prompt))

    def _get_rag_context(self, query: str) -> str:
        """获取RAG检索上下文"""
        if self.rag is None:
            return ""

        try:
            context = self.rag.get_relevant_context(query, max_context_length=1500)
            if context.strip():
                logger.debug(f"RAG检索到相关内容，长度: {len(context)}")
                return context
            else:
                logger.debug("RAG未检索到相关内容")
                return ""
        except Exception as e:
            logger.error(f"RAG检索出错: {e}")
            return ""

    def _duplex(self):
        # 处理识别结果
        data = self.vad_queue.get()
        # 识别到vad开始
        if self.vad_start:
            self.speech.append(data)
        vad_status = data.get("vad_statue")
        # 空闲的时候，取出耗时任务进行播放
        if (
            hasattr(self, "task_queue")
            and not self.task_queue.empty()
            and not self.vad_start
            and vad_status is None
            and not self.player.get_playing_status()
            and self.chat_lock is False
        ):
            result = self.task_queue.get()
            future = self.executor.submit(self.speak_and_play, result.response)
            self.tts_queue.put(future)

        """ 语音唤醒
        if time.time() - self.start_time>=60:
            self.silence_status = True

        if self.silence_status:
            return
        """
        if vad_status is None:
            return
        if "start" in vad_status:
            if (
                self.player.get_playing_status() or self.chat_lock is True
            ):  # 正在播放，打断场景
                if self.INTERRUPT:
                    self.chat_lock = False
                    self.interrupt_playback()
                    self.vad_start = True
                    self.speech.append(data)
                else:
                    return
            else:  # 没有播放，正常
                self.vad_start = True
                self.speech.append(data)
        elif "end" in vad_status and len(self.speech) > 0:
            try:
                logger.debug(f"语音包的长度：{len(self.speech)}")
                self.vad_start = False
                voice_data = [d["voice"] for d in self.speech]
                text, tmpfile = self.asr.recognizer(voice_data)
                self.speech = []
            except Exception as e:
                self.vad_start = False
                self.speech = []
                logger.error(f"ASR识别出错: {e}")
                return
            if not text.strip():
                logger.debug("识别结果为空，跳过处理。")
                return

            logger.debug(f"ASR识别结果: {text}")
            if self.callback:
                self.callback({"role": "user", "content": str(text)})
            self.executor.submit(self.chat, text)
        return True

    def run(self):
        try:
            self.start_recording_and_vad()  # 监听语音流
            while not self.stop_event.is_set():
                self._duplex()  # 双工处理
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt. Exiting...")
        finally:
            self.shutdown()

    def speak_and_play(self, text):
        if text is None or len(text) <= 0:
            logger.info(f"无需tts转换，query为空，{text}")
            return None
        tts_file = self.tts.to_tts(text)
        if tts_file is None:
            logger.error(f"tts转换失败，{text}")
            return None
        logger.debug(f"TTS 文件生成完毕{self.chat_lock}")
        # if self.chat_lock is False:
        #    return None
        # 开始播放
        # self.player.play(tts_file)
        # return True
        return tts_file

    def chat(self, query):
        # 获取RAG上下文
        rag_context = self._get_rag_context(query)

        # 更新系统提示词包含RAG上下文
        self._update_system_prompt(rag_context)

        self.dialogue.put(Message(role="user", content=query))
        response_message = []
        start = 0
        self.chat_lock = True

        if hasattr(self, "start_task_mode") and self.start_task_mode:
            response_message = self.chat_tool(query)
        else:
            # 提交 LLM 任务
            try:
                start_time = time.time()  # 记录开始时间
                llm_responses = self.llm.response(self.dialogue.get_llm_dialogue())
            except Exception as e:
                self.chat_lock = False
                logger.error(f"LLM 处理出错 {query}: {e}")
                return None
            # 提交 TTS 任务到线程池
            for content in llm_responses:
                response_message.append(content)
                end_time = time.time()  # 记录结束时间
                logger.debug(
                    f"大模型返回时间时间: {end_time - start_time} 秒, 生成token={content}"
                )
                if is_segment(response_message):
                    segment_text = "".join(response_message[start:])
                    # 为了保证语音的连贯，至少2个字才转tts
                    if len(segment_text) <= max(2, start):
                        continue
                    future = self.executor.submit(self.speak_and_play, segment_text)
                    self.tts_queue.put(future)
                    start = len(response_message)

            # 处理剩余的响应
            if start < len(response_message):
                segment_text = "".join(response_message[start:])
                future = self.executor.submit(self.speak_and_play, segment_text)
                self.tts_queue.put(future)

        self.chat_lock = False
        # 更新对话
        if self.callback:
            self.callback({"role": "assistant", "content": "".join(response_message)})
        self.dialogue.put(Message(role="assistant", content="".join(response_message)))
        self.dialogue.dump_dialogue()
        logger.debug(
            json.dumps(self.dialogue.get_llm_dialogue(), indent=4, ensure_ascii=False)
        )
        return True

    def mcp(self):
        """
        调用MCP模式
            尽在模型支持函数调用的情况下使用
        TODO: MCP 模式的实现
        """
        pass


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="百聆机器人")

    # Add arguments
    parser.add_argument("config_path", type=str, help="配置文件", default=None)

    # Parse arguments
    args = parser.parse_args()
    config_path = args.config_path

    # 创建 Robot 实例并运行
    robot = Robot(config_path)
    robot.run()
