import click
from rich import print
from rich.table import Table
from datetime import datetime
from src.agent import analyze_task
from src.db_manager import init_db, SessionLocal, add_task, update_task, list_tasks
from src.vector_store import add_or_update_vector, search


@click.group()
def cli():
    """Main CLI entry point."""
    init_db()
    print("[bold green] Database initialized successfully![/bold green]")


# ADD COMMAND (with optional --due flag)
@cli.command()
@click.argument("text", nargs=-1)
@click.option("--due", "due_date", help="Optional due date in YYYY-MM-DD format")
def add(text, due_date):
    """Add a task from natural language input (optionally include a due date)."""
    task_text = " ".join(text).strip()
    if not task_text:
        print("[red] Please provide a task description.[/red]")
        return

    try:
        print("[blue] Analyzing your task with the AI agent...[/blue]")
        data = analyze_task(task_text)

        # Handle optional due date
        if due_date:
            try:
                parsed_date = datetime.strptime(due_date, "%Y-%m-%d").date()
                data["due_date_iso"] = parsed_date.isoformat()
            except ValueError:
                print("[yellow]⚠️ Invalid date format. Use YYYY-MM-DD (e.g., 2025-11-10).[/yellow]")
                data["due_date_iso"] = None
        else:
            data["due_date_iso"] = None

        # Save to DB
        with SessionLocal() as s:
            obj = add_task(s, data)

            # Safely prepare text for embedding
            task_text_to_embed = f"{obj.title}. {obj.description or ''}".strip()
            if task_text_to_embed:
                add_or_update_vector(
                    obj.id,
                    task_text_to_embed,
                    {
                        "category": obj.category,
                        "priority": obj.priority,
                        "status": obj.status,
                        "due_date": data["due_date_iso"],
                    },
                )
                print(f"[green] Task added and embedded successfully![/green]")
            else:
                print(f"[yellow] Skipping embedding — no valid text for task {obj.id}[/yellow]")

            print({
                "id": obj.id,
                "title": obj.title,
                "category": obj.category,
                "priority": obj.priority,
                "status": obj.status,
                "due_date": data["due_date_iso"],
            })

    except Exception as e:
        print(f"[red] Error while adding task:[/red] {e}")


# =========================================================
# FIND COMMAND
# =========================================================
@cli.command()
@click.option("--q", "query", required=True, help="Semantic search query")
@click.option("--k", default=5, show_default=True)
def find(query, k):
    """Semantic search across tasks using vector embeddings."""
    try:
        print(f"[blue] Searching for tasks similar to:[/blue] '{query}'")
        res = search(query, k=k)
        if not res or not res.get("ids"):
            print("[yellow] No matching tasks found.[/yellow]")
            return

        for i, doc in enumerate(res["documents"][0]):
            print(f"[green]Result {i + 1}:[/green] {doc}")

    except Exception as e:
        print(f"[red] Search failed:[/red] {e}")

# LIST COMMAND
@cli.command()
@click.option("--status", help="Filter by task status")
@click.option("--category", help="Filter by task category")
@click.option("--priority", help="Filter by task priority")
@click.option("--due", help="Filter by specific due date (YYYY-MM-DD)")
def list(status, category, priority, due):
    """List tasks with optional filters (including due date)."""
    try:
        filters = {"status": status, "category": category, "priority": priority}

        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
                filters["due_date_iso"] = due
            except ValueError:
                print("[yellow] Invalid due date filter. Use YYYY-MM-DD.[/yellow]")

        with SessionLocal() as s:
            items = list_tasks(s, filters)
            if not items:
                print("[yellow] No tasks found for given filters.[/yellow]")
                return

            table = Table(title=" Current Tasks", show_lines=True)
            table.add_column("ID", justify="center")
            table.add_column("Title")
            table.add_column("Category")
            table.add_column("Priority", justify="center")
            table.add_column("Status", justify="center")
            table.add_column("Due Date", justify="center")

            for t in items:
                table.add_row(
                    str(t.id),
                    t.title or "-",
                    t.category or "-",
                    t.priority or "-",
                    t.status or "-",
                    str(t.due_date_iso or "-"),
                )

            print(table)
    except Exception as e:
        print(f"[red] Failed to list tasks:[/red] {e}")


# UPDATE COMMAND
@cli.command()
@click.argument("task_id", type=int)
@click.option("--status", help="Update task status (Pending, In-Progress, Done)")
@click.option("--priority", help="Update task priority (High, Medium, Low)")
@click.option("--category", help="Update category")
@click.option("--title", help="Update title")
@click.option("--description", help="Update description")
@click.option("--due", help="Update due date (YYYY-MM-DD)")
def update(task_id, **updates):
    """Update a task’s fields by ID."""
    if updates.get("due"):
        try:
            parsed_date = datetime.strptime(updates["due"], "%Y-%m-%d").date()
            updates["due_date_iso"] = parsed_date.isoformat()
        except ValueError:
            print("[yellow] Invalid date format. Use YYYY-MM-DD.[/yellow]")
        del updates["due"]

    updates = {k: v for k, v in updates.items() if v is not None}

    if not updates:
        print("[yellow] No updates provided.[/yellow]")
        return

    try:
        with SessionLocal() as s:
            obj = update_task(s, task_id, updates)
            if obj:
                # Re-embed updated text
                task_text_to_embed = f"{obj.title}. {obj.description or ''}".strip()
                if task_text_to_embed:
                    add_or_update_vector(
                        obj.id,
                        task_text_to_embed,
                        {
                            "category": obj.category,
                            "priority": obj.priority,
                            "status": obj.status,
                            "due_date": obj.due_date_iso,
                        },
                    )
                print(f"[green] Task {task_id} updated successfully![/green]")
                print({
                    "id": obj.id,
                    "title": obj.title,
                    "category": obj.category,
                    "priority": obj.priority,
                    "status": obj.status,
                    "due_date": obj.due_date_iso,
                })
            else:
                print("[red] Task not found.[/red]")
    except Exception as e:
        print(f"[red] Update failed:[/red] {e}")

# DELETE COMMAND (Safe + Windows Compatible)
@cli.command()
@click.argument("task_ids", nargs=-1, type=int)
@click.option("--all", "delete_all", is_flag=True, help="Delete ALL tasks and vectors")
def delete(task_ids, delete_all):
    """Delete tasks by ID or remove all tasks if --all is given."""
    from src.db_manager import Task
    from src.vector_store import get_vector_client
    import os, shutil, time, chromadb

    def safe_rmtree(path, retries=3):
        """Safe Windows-compatible folder removal with retries."""
        for i in range(retries):
            try:
                shutil.rmtree(path)
                return True
            except PermissionError:
                print(f"[yellow] Folder locked (attempt {i+1}/{retries}), retrying...[/yellow]")
                time.sleep(1)
        print(f"[red] Failed to delete folder {path} after retries.[/red]")
        return False

    with SessionLocal() as s:
        if delete_all:
            confirm = input(" This will delete ALL tasks and embeddings. Type 'yes' to confirm: ")
            if confirm.lower() != "yes":
                print("[yellow] Deletion cancelled.[/yellow]")
                return

            s.query(Task).delete()
            s.commit()
            print("[red] Deleted all tasks from the database.[/red]")

            chroma_path = "data/chroma"
            if os.path.exists(chroma_path):
                try:
                    print("[yellow] Closing Chroma client before deletion...[/yellow]")
                    client = chromadb.PersistentClient(path=chroma_path)
                    client._system.stop()
                except Exception as e:
                    print(f"[yellow] Warning while closing Chroma client:[/yellow] {e}")
                safe_rmtree(chroma_path)
                print("[red] Cleared all embeddings from Chroma vector store.[/red]")

            print("[bold green] All tasks and vectors deleted successfully![/bold green]")
            return

        if not task_ids:
            print("[yellow] Please provide one or more task IDs or use --all.[/yellow]")
            return

        client = get_vector_client()
        collection = client.get_or_create_collection("tasks")

        for tid in task_ids:
            task = s.get(Task, tid)
            if task:
                s.delete(task)
                s.commit()
                try:
                    collection.delete(ids=[str(tid)])
                    print(f"[red] Deleted embedding for Task ID {tid}[/red]")
                except Exception:
                    print(f"[yellow] Could not delete embedding for Task ID {tid}[/yellow]")
                print(f"[red] Deleted Task ID {tid}: {task.title}[/red]")
            else:
                print(f"[yellow] Task ID {tid} not found.[/yellow]")

    print("[green] Deletion process complete![/green]")


# ENTRY POINT
if __name__ == "__main__":
    cli()