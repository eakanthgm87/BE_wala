from project_reader import ProjectReader

SYSTEM_EXPLAINER = """You are ShellMind's project analyst. Given a codebase snapshot, produce a
thorough explanation covering:
1. What the project does (purpose & goals)
2. Architecture & major components
3. Data flow between modules
4. Key design decisions and patterns used
5. Dependencies and external integrations
6. Potential weaknesses or areas to improve
Be specific, cite actual filenames and function names, and avoid vague statements."""


class ProjectExplainer:
    def __init__(self, project_root: str | None = None):
        self.reader = ProjectReader(project_root)

    def build_explain_prompt(self) -> str:
        tree = self.reader.get_tree()
        context = self.reader.build_context()

        return (
            f"Here is the directory structure:\n\n{tree}\n\n"
            f"Here are the file contents:\n\n{context}\n\n"
            "Please explain this project thoroughly."
        )

    def get_system_prompt(self) -> str:
        return SYSTEM_EXPLAINER