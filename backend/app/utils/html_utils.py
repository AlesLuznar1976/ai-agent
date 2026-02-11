"""HTML čiščenje za email vsebino iz MS Graph."""

import re


def strip_html_to_text(html: str) -> str:
    """Pretvori HTML v čist tekst za LLM procesiranje.

    MS Graph vrača email body kot HTML. LLM slabo procesira
    HTML tage, zato jih moramo odstraniti.
    """
    if not html:
        return ""

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Odstrani script in style elemente
        for element in soup(["script", "style", "head"]):
            element.decompose()

        # Pretvori <br> in <p> v newline
        for br in soup.find_all("br"):
            br.replace_with("\n")
        for p in soup.find_all("p"):
            p.insert_after("\n")

        text = soup.get_text(separator=" ")
    except ImportError:
        # Fallback brez BeautifulSoup
        text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
        text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)

    # Počisti whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text
