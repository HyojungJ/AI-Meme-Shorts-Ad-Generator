from content_pipeline.db import test_db_connection


def main() -> int:
    db_name, db_user, now = test_db_connection()
    print(f"ok db={db_name} user={db_user} time={now}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
