import re


class EntityExtractor:
    def extract_project_name(self, user_request: str):
        pattern = r"פרויקט\s+([\u0590-\u05FF\w\s]+)"

        match = re.search(pattern, user_request)

        if match:
            return match.group(1).strip()

        return None