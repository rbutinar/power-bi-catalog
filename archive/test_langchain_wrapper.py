from pbi_semantic_analyzer.langchain_wrapper import PBISemanticAnalyzerTool

if __name__ == "__main__":
    tool = PBISemanticAnalyzerTool()
    # Puoi passare config_path se vuoi usare un file diverso da .env
    result = tool._run()
    print(result)
