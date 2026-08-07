"""
Database query tool implementation.
"""
from sqlalchemy import text

from app.services.tools.base import Tool, ToolContext, ToolError


class DatabaseQueryTool(Tool):
    name = "database_query"
    description = "Executes read-only SQL queries to inspect system tables and database schemas."

    async def run(self, input_text: str, context: ToolContext) -> str:
        query = input_text.strip()
        if not query:
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE();"

        # Restrict to read-only queries for database safety
        upper_query = query.upper()
        if any(keyword in upper_query for keyword in ["DROP ", "TRUNCATE ", "DELETE ", "ALTER "]):
            raise ToolError("Destructive SQL commands (DROP/TRUNCATE/DELETE/ALTER) are disabled.")

        try:
            result = await context.session.execute(text(query))
            if result.returns_rows:
                rows = result.fetchall()
                keys = result.keys()
                header = " | ".join(keys)
                row_lines = [" | ".join(str(val) for val in row) for row in rows[:50]]
                return f"SQL Query: {query}\n\n{header}\n" + "-" * len(header) + "\n" + "\n".join(row_lines)
            else:
                return f"SQL Statement executed successfully. Rows affected: {result.rowcount}"
        except Exception as exc:
            raise ToolError(f"Database query execution failed: {exc}")
