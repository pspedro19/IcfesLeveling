import os
import json
import sys

from app.import_icfes_excel import ICFESExcelImporter
from app.core.database import get_db
from app.models.question import Question


def strtobool(value: str) -> bool:
    return str(value).lower() in ("1", "true", "yes", "y")


def main() -> None:
    db = next(get_db())
    excel_path = os.environ.get("QUESTIONS_EXCEL_PATH", "/app/ICFES2 (1).xlsx")
    clear_existing = strtobool(os.environ.get("IMPORT_CLEAR_EXISTING", "false"))

    summary = {"ok": False, "excel_path": excel_path}
    try:
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel file not found at: {excel_path}")

        if clear_existing:
            db.query(Question).delete()
            db.commit()

        importer = ICFESExcelImporter(db)
        result = importer.import_excel(excel_path, validate_only=False)

        total_questions = db.query(Question).count()
        summary.update({
            "ok": True,
            "result": result,
            "db_total_questions": total_questions,
        })
        print(json.dumps(summary))
    except Exception as exc:
        summary.update({"error": str(exc)})
        print(json.dumps(summary))
        sys.exit(1)


if __name__ == "__main__":
    main()


