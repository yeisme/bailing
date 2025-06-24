from abc import ABC, abstractmethod
import openai


from bailing import logger


class LLM(ABC):
    @abstractmethod
    def response(self, dialogue):
        pass

    def response_call(self, dialogue, functions_call):
        # 默认降级实现：直接调用 response，tool_calls 设为 None
        for chunk in self.response(dialogue):
            yield chunk, None


class OpenAILLM(LLM):
    def __init__(self, config):
        self.model_name = config.get("model_name")
        self.api_key = config.get("api_key")
        self.base_url = config.get("url")
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        # 检查是否支持 function call
        self.supports_function_call = True
        # 可以根据模型名或配置判断是否支持 function call
        # 这里假设所有 openai 模型都支持，如需更细致可扩展

    def response(self, dialogue):
        try:
            responses = self.client.chat.completions.create(
                model=self.model_name, messages=dialogue, stream=True
            )
            for chunk in responses:
                yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error in response generation: {e}")

    def response_call(self, dialogue, functions_call):
        if not getattr(self, "supports_function_call", True):
            # 不支持 function call，降级为普通 response
            for chunk in self.response(dialogue):
                yield chunk, None
            return
        try:
            responses = self.client.chat.completions.create(
                model=self.model_name,
                messages=dialogue,
                stream=True,
                tools=functions_call,
            )
            for chunk in responses:
                yield chunk.choices[0].delta.content, chunk.choices[0].delta.tool_calls
        except Exception as e:
            logger.error(f"Error in response generation: {e}")


def create_instance(class_name, *args, **kwargs):
    # 获取类对象
    cls = globals().get(class_name)
    if cls:
        # 创建并返回实例
        return cls(*args, **kwargs)
    else:
        raise ValueError(f"Class {class_name} not found")


if __name__ == "__main__":
    # 创建 DeepSeekLLM 的实例
    deepseek = create_instance(
        "DeepSeekLLM", api_key="your_api_key", base_url="your_base_url"
    )
    dialogue = [{"role": "user", "content": "hello"}]

    # 打印逐步生成的响应内容
    for chunk in deepseek.response(dialogue):
        print(chunk)
