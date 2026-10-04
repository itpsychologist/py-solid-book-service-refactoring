import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, TypeVar


@dataclass
class Book:
    title: str
    content: str


# ===================== Відображення =====================
class Displayer(ABC):
    @abstractmethod
    def display(self, book: Book) -> None: ...


class ConsoleDisplayer(Displayer):
    def display(self, book: Book) -> None:
        print(book.content)


class ReverseDisplayer(Displayer):
    def display(self, book: Book) -> None:
        print(book.content[::-1])


# ===================== Друк =====================
class Printer(ABC):
    @abstractmethod
    def print_book(self, book: Book) -> None: ...


class HeaderPrinter(Printer):

    def __init__(self, header_template: str, displayer: Displayer):
        self._header_template = header_template
        self._displayer = displayer

    def print_book(self, book: Book) -> None:
        print(self._header_template.format(title=book.title))
        self._displayer.display(book)


# ===================== Серіалізація =====================
class Serializer(ABC):
    @abstractmethod
    def serialize(self, book: Book) -> str: ...


class JsonSerializer(Serializer):
    def serialize(self, book: Book) -> str:
        return json.dumps({"title": book.title, "content": book.content})


class XmlSerializer(Serializer):
    def serialize(self, book: Book) -> str:
        root = ET.Element("book")
        ET.SubElement(root, "title").text = book.title
        ET.SubElement(root, "content").text = book.content
        return ET.tostring(root, encoding="unicode")


# ===================== Вибір стратегії =====================
T = TypeVar("T")


def get_strategy(registry: Mapping[str, T], key: str, kind: str) -> T:
    try:
        return registry[key]
    except KeyError:
        raise ValueError(f"Unknown {kind} type: {key}") from None


# ===================== Команди =====================
class Command(ABC):
    @abstractmethod
    def execute(self, book: Book, method_type: str) -> str | None: ...


class DisplayCommand(Command):
    def __init__(self, displayers: Mapping[str, Displayer]):
        self._displayers = displayers

    def execute(self, book: Book, method_type: str) -> None:
        get_strategy(self._displayers, method_type, "display").display(book)


class PrintCommand(Command):
    def __init__(self, printers: Mapping[str, Printer]):
        self._printers = printers

    def execute(self, book: Book, method_type: str) -> None:
        get_strategy(self._printers, method_type, "print").print_book(book)


class SerializeCommand(Command):
    def __init__(self, serializers: Mapping[str, Serializer]):
        self._serializers = serializers

    def execute(self, book: Book, method_type: str) -> str:
        return get_strategy(self._serializers, method_type, "serialize").serialize(book)


# ===================== Збірка (composition root) =====================
def build_default_commands() -> dict[str, Command]:
    displayers: dict[str, Displayer] = {
        "console": ConsoleDisplayer(),
        "reverse": ReverseDisplayer(),
    }
    printers: dict[str, Printer] = {
        "console": HeaderPrinter("Printing the book: {title}...", displayers["console"]),
        "reverse": HeaderPrinter("Printing the book in reverse: {title}...", displayers["reverse"]),
    }
    serializers: dict[str, Serializer] = {
        "json": JsonSerializer(),
        "xml": XmlSerializer(),
    }
    return {
        "display": DisplayCommand(displayers),
        "print": PrintCommand(printers),
        "serialize": SerializeCommand(serializers),
    }


def main(
        book: Book,
        commands: list[tuple[str, str]],
        handlers: Mapping[str, Command] | None = None,
) -> None | str:
    handlers = handlers if handlers is not None else build_default_commands()
    for cmd, method_type in commands:
        handler = handlers.get(cmd)
        if handler is None:
            continue  # як і в оригіналі: невідомі команди ігноруються
        result = handler.execute(book, method_type)
        if result is not None:
            return result
    return None


if __name__ == "__main__":
    sample_book = Book("Sample Book", "This is some sample content.")
    print(main(sample_book, [("display", "reverse"), ("serialize", "xml")]))