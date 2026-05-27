from core.database import get_connection


class SnippetController:
    def list_snippets(self, language=None, search=None):
        conn = get_connection()
        try:
            conditions, params = [], []
            if language:
                conditions.append("language=?")
                params.append(language)
            if search:
                conditions.append("(title LIKE ? OR description LIKE ? OR code LIKE ?)")
                params += [f"%{search}%", f"%{search}%", f"%{search}%"]
            query = "SELECT * FROM snippets"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY created_at DESC"
            return [dict(r) for r in conn.execute(query, params).fetchall()]
        finally:
            conn.close()

    def add_snippet(self, title, language, code, description, project_id=None):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO snippets (title, language, code, description, project_id) VALUES (?,?,?,?,?)",
                (title, language, code, description, project_id),
            )
            conn.commit()
        finally:
            conn.close()

    def update_snippet(self, id, title, language, code, description):
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE snippets SET title=?, language=?, code=?, description=? WHERE id=?",
                (title, language, code, description, id),
            )
            conn.commit()
        finally:
            conn.close()

    def delete_snippet(self, id):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM snippets WHERE id=?", (id,))
            conn.commit()
        finally:
            conn.close()

    def get_by_id(self, id):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM snippets WHERE id=?", (id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
