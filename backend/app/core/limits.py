"""Size limits shared by the API schemas and the database columns."""

# Column size for repo_url. The enforced cap is the max_repo_url_length setting, which may be
# raised up to this size without a migration. 2048 is the practical maximum URL length.
REPO_URL_COLUMN_LENGTH = 2048

MAX_EVIDENCE_EXCERPT_LENGTH = 1000
MAX_SOURCE_LOCATION_LENGTH = 500
MAX_TITLE_LENGTH = 200
MAX_STATEMENT_LENGTH = 2000

MAX_CODE_LENGTH = 50
