from backend.config import DEFAULT_SYSTEM_PROMPT, HISTORY_FILE
from backend.tools import get_all_tools
from backend.memory import HistoryManager, CheckpointerProvider
from backend.agent import ChatBot


class CLIChat:
    def __init__(self):
        self.history = HistoryManager(file_path=HISTORY_FILE)
        self.bot = ChatBot(
            tools=get_all_tools(),
            history_manager=self.history,
            checkpointer=CheckpointerProvider().get(),
        )

    def run(self, chat_id: int = 0, sys_msg: str = DEFAULT_SYSTEM_PROMPT):
        thread_id = chat_id or self.history.current_id

        print(f"Chat started. Thread ID: {thread_id}")
        print("Type 'q' to quit.\n")

        while True:
            try:
                user_msg = input("user: ")
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if user_msg.lower() == "q":
                print("Goodbye!")
                break
            if not user_msg.strip():
                continue

            result = self.bot.chat_sync(thread_id, user_msg, sys_msg)
            msgs = result.get("messages", [])
            if not msgs:
                print("Assistant: [no response]\n")
                continue
            self.history.add(thread_id, msgs)
            print(f"Assistant: {msgs[-1].content}\n")

        self.history.update()


def main():
    cli = CLIChat()
    cli.run(chat_id=1)


if __name__ == "__main__":
    main()
