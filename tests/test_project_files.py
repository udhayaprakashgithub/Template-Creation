from pathlib import Path
import unittest


class ProjectFilesTest(unittest.TestCase):
    def test_core_project_files_exist(self):
        expected = [
            Path("manage.py"),
            Path("project_config/settings.py"),
            Path("project_config/urls.py"),
            Path("project_config/wsgi.py"),
            Path("project_config/asgi.py"),
            Path("document_processor/models.py"),
            Path("document_processor/views.py"),
            Path("document_processor/migrations/0001_initial.py"),
            Path("requirements.txt"),
            Path("README.md"),
        ]
        for file_path in expected:
            self.assertTrue(file_path.exists(), f"Missing file: {file_path}")


if __name__ == "__main__":
    unittest.main()
