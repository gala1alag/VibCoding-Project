from core.database import get_connection

_PRIORITY_ORDER = "CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END"


class TodoController:
    def list_todos(self, project_id=None):
        conn = get_connection()
        try:
            if project_id:
                rows = conn.execute(
                    f"SELECT * FROM todos WHERE project_id=? ORDER BY {_PRIORITY_ORDER}, created_at DESC",
                    (project_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    f"SELECT * FROM todos ORDER BY {_PRIORITY_ORDER}, created_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_todo(self, title, description="", status="todo", priority="medium", due_date=None, project_id=None):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO todos (title, description, status, priority, due_date, project_id) VALUES (?,?,?,?,?,?)",
                (title, description, status, priority, due_date, project_id),
            )
            conn.commit()
        finally:
            conn.close()

    def update_todo(self, id, **kwargs):
        if not kwargs:
            return
        conn = get_connection()
        try:
            fields = ", ".join(f"{k}=?" for k in kwargs)
            conn.execute(f"UPDATE todos SET {fields} WHERE id=?", [*kwargs.values(), id])
            conn.commit()
        finally:
            conn.close()

    def delete_todo(self, id):
        conn = get_connection()
        try:
            conn.execute("DELETE FROM todos WHERE id=?", (id,))
            conn.commit()
        finally:
            conn.close()

    def move_todo(self, todo_id, status):
        self.update_todo(todo_id, status=status)
