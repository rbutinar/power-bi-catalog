from langchain.tools import BaseTool
from .config import Config
from .analyzer import PBISemanticAnalyzer

class PBISemanticAnalyzerTool(BaseTool):
    name: str = "pbi_semantic_analyzer"
    description: str = "Analizza i modelli semantici Power BI di uno o più workspace e restituisce un JSON strutturato."

    def _run(self, config_path: str = ".env"):
        config = Config(env_path=config_path)
        analyzer = PBISemanticAnalyzer(config)
        output = analyzer.analyze()
        return output.json()

    async def _arun(self, config_path: str = ".env"):
        return self._run(config_path)
