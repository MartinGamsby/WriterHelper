# The FR/EN article pair and cross-language operations. No Qt.
from deep_translator import GoogleTranslator

from article import ArticleModel


# ========================================================================================
class ArticlesModel:

    # ====================================================================================
    def __init__(self, french: ArticleModel, english: ArticleModel):
        self.french = french
        self.english = english

    # ====================================================================================
    @staticmethod
    def create(config_dir="."):
        french = ArticleModel(hl="fr", config_dir=config_dir)
        english = ArticleModel(hl="en", config_dir=config_dir)
        french.set_ref(english)
        english.set_ref(french)
        return ArticlesModel(french, english)

    # ====================================================================================
    def fr(self):
        return self.french

    def en(self):
        return self.english

    def get(self, hl):
        return self.english if hl == "en" else self.french

    # ====================================================================================
    def translate(self, hl):
        """Translate the `hl` article into the other language. Refuses to overwrite
        a destination that already has content."""
        print("translate", hl)
        if hl == "en":
            src, dst, dst_hl = self.en(), self.fr(), "fr"
        else:
            src, dst, dst_hl = self.fr(), self.en(), "en"

        if dst.content:
            print("DESTINATION ALREADY HAS CONTENT!!")
            return False

        if src.title:
            dst.set_title(GoogleTranslator(source=hl, target=dst_hl).translate(src.title))
        if src.content:
            dst.set_content(GoogleTranslator(source=hl, target=dst_hl).translate(src.content))
        if src.tags:
            dst.set_tags(GoogleTranslator(source=hl, target=dst_hl).translate(src.tags))
        if src.get_excerpt_img():
            dst.set_excerpt_img(src.get_excerpt_img())
        if src.get_date():
            dst.set_date(src.get_date())
        return True
