"""Interactive CLI Loglan Grammar Assistant powered by Gemma & LOD."""

import argparse
import sys

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt
except ImportError:
    Console = None  # Fallback to plain print if rich is not present

try:
    from src.config import DEFAULT_MODEL, DB_PATH
    from src.retriever import LoglanRetriever
    from src.prompts import (
        SYSTEM_PROMPT,
        DISAMBIGUATION_PROMPT_TEMPLATE,
        SLOT_IDENTIFICATION_PROMPT_TEMPLATE,
        BENCHMARK_PROMPT_TEMPLATE,
    )
    from src.models import get_model_provider, BaseLLMProvider
except ImportError:
    from config import DEFAULT_MODEL, DB_PATH
    from retriever import LoglanRetriever
    from prompts import (
        SYSTEM_PROMPT,
        DISAMBIGUATION_PROMPT_TEMPLATE,
        SLOT_IDENTIFICATION_PROMPT_TEMPLATE,
        BENCHMARK_PROMPT_TEMPLATE,
    )
    from models import get_model_provider, BaseLLMProvider


class LoglanAssistant:
    """End-to-end Assistant coordinating RAG retrieval, prompt construction, and LLM inference."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        provider_name: str = "auto",
        mock: bool = False,
        db_path: str = str(DB_PATH)
    ):
        self.retriever = LoglanRetriever(db_path=db_path)
        self.provider: BaseLLMProvider = get_model_provider(
            model_name=model_name,
            provider=provider_name,
            mock=mock
        )
        self.console = Console() if Console else None

    def ask(self, question: str) -> str:
        """Process a general user question with full RAG grounding."""
        context = self.retriever.retrieve_context(question)
        prompt = BENCHMARK_PROMPT_TEMPLATE.format(question=question, context=context)
        resp = self.provider.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        return resp.content

    def explain_slots(self, word: str, sentence: str = "") -> str:
        """Directly explain argument slots for a given predicate."""
        context = self.retriever.retrieve_context(word)
        sent = sentence if sentence else f"Example usage with {word}"
        prompt = SLOT_IDENTIFICATION_PROMPT_TEMPLATE.format(
            predicate=word,
            sentence=sent,
            context=context
        )
        resp = self.provider.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        return resp.content

    def compare_ambiguity(self, english: str, loglan: str = "") -> str:
        """Analyze syntactic ambiguity: English vs Loglan."""
        context = self.retriever.retrieve_context(english + " " + loglan)
        prompt = DISAMBIGUATION_PROMPT_TEMPLATE.format(
            english=english,
            loglan=loglan or "Corresponding Loglan expression(s)",
            context=context
        )
        resp = self.provider.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        return resp.content

    def display_word_info(self, word: str):
        """Display raw dictionary entries in a formatted table."""
        entries = self.retriever.search_dictionary(word, limit=5)
        if not entries:
            print(f"No dictionary entry found for '{word}'.")
            return

        if self.console:
            table = Table(title=f"LOD Dictionary: '{word}'", show_header=True, header_style="bold magenta")
            table.add_column("Word", style="bold cyan")
            table.add_column("Type", style="green")
            table.add_column("Slots/Grammar", style="yellow")
            table.add_column("Definition & Usage", style="white")

            for e in entries:
                slots = e.get("slots") or ""
                code = e.get("grammar_code") or ""
                grammar_str = f"[{slots}{code}]" if (slots or code) else ""
                body = e.get("body", "")
                if e.get("usage"):
                    body += f"\nUsage: {e['usage']}"
                if e.get("components"):
                    body += f"\nAffixes: {', '.join(e['components'])}"
                table.add_row(e["name"], str(e["type"]), grammar_str, body)
            self.console.print(table)
        else:
            for e in entries:
                print(f"[{e['name']} ({e['type']})] {e.get('body')}")


def run_interactive(assistant: LoglanAssistant):
    """Run interactive REPL loop."""
    console = assistant.console or Console()
    console.print(Panel.fit(
        "[bold cyan]Loglan Grammar Assistant (Gemma & LOD)[/bold cyan]\n"
        "Zero Syntactic Ambiguity • First-Order Predicate Logic • 10,000+ Words\n\n"
        "Type [green]/help[/green] to list commands or ask any question directly.",
        border_style="cyan"
    ))

    while True:
        try:
            user_input = Prompt.ask("\n[bold yellow]Loglan>[/bold yellow]").strip()
            if not user_input:
                continue

            if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
                console.print("[dim]Hoi vi (Goodbye)![/dim]")
                break

            if user_input.startswith("/help"):
                console.print(
                    "[bold]Available Commands:[/bold]\n"
                    "  [green]/ask <question>[/green]          Ask any grammar or translation question\n"
                    "  [green]/word <word>[/green]              Lookup dictionary definition in LOD\n"
                    "  [green]/slots <word>[/green]             Analyze predicate slots (x1, x2, x3...)\n"
                    "  [green]/compare <english>[/green]        Compare English ambiguity vs Loglan zero ambiguity\n"
                    "  [green]/context <query>[/green]          Inspect raw RAG context for a query\n"
                    "  [green]/exit[/green]                     Quit the assistant\n"
                )
            elif user_input.startswith("/word "):
                word = user_input[6:].strip()
                assistant.display_word_info(word)
            elif user_input.startswith("/slots "):
                word = user_input[7:].strip()
                with console.status(f"[bold green]Analyzing slots for '{word}'..."):
                    result = assistant.explain_slots(word)
                console.print(Markdown(result))
            elif user_input.startswith("/compare "):
                phrase = user_input[9:].strip()
                with console.status(f"[bold green]Analyzing ambiguities for '{phrase}'..."):
                    result = assistant.compare_ambiguity(phrase)
                console.print(Markdown(result))
            elif user_input.startswith("/context "):
                q = user_input[9:].strip()
                ctx = assistant.retriever.retrieve_context(q)
                console.print(Panel(ctx, title=f"RAG Context for: {q}", border_style="dim"))
            else:
                q = user_input[5:].strip() if user_input.startswith("/ask ") else user_input
                with console.status("[bold green]Querying Gemma with LOD grounding..."):
                    result = assistant.ask(q)
                console.print(Markdown(result))

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Hoi vi (Goodbye)![/dim]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


def main():
    parser = argparse.ArgumentParser(description="Loglan Grammar Assistant (Gemma & LOD)")
    parser.add_argument("--query", "-q", type=str, help="Single question to answer")
    parser.add_argument("--word", "-w", type=str, help="Lookup word definition")
    parser.add_argument("--slots", "-s", type=str, help="Show predicate slots")
    parser.add_argument("--compare", "-c", type=str, help="Compare English ambiguity vs Loglan")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive REPL")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Model name (e.g. gemma-3-27b-it)")
    parser.add_argument("--provider", type=str, default="auto", help="Provider (auto, google, ollama, mock)")
    parser.add_argument("--mock", action="store_true", help="Use deterministic mock provider")
    args = parser.parse_args()

    assistant = LoglanAssistant(
        model_name=args.model,
        provider_name=args.provider,
        mock=args.mock
    )

    if args.word:
        assistant.display_word_info(args.word)
    elif args.slots:
        print(assistant.explain_slots(args.slots))
    elif args.compare:
        print(assistant.compare_ambiguity(args.compare))
    elif args.query:
        print(assistant.ask(args.query))
    else:
        run_interactive(assistant)


if __name__ == "__main__":
    main()
