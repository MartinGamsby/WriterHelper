from dataclasses import dataclass

@dataclass
class ArticleModel:
    title: str = ""
    content: str = ""

    def content_md(self) -> str:
        return "# %s\n\n%s" % (self.title, self.content)
        