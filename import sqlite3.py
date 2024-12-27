import sqlite3
from graphviz import Digraph

def fetch_schema(cursor):
    schema = {}

    # Fetch tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        schema[table_name] = []
        # Fetch columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        schema[table_name] = [{'name': col[1], 'type': col[2]} for col in columns]

    return schema

def visualize_schema(schema):
    dot = Digraph(comment="Database Schema")

    for table_name, columns in schema.items():
        dot.node(table_name, table_name)
        for column in columns:
            dot.edge(table_name, f"{table_name}_{column['name']}")

    dot.render('database_schema', format='png', cleanup=True)
    print("Структурная схема базы данных сохранена в файл 'database_schema.png'")

def print_schema(schema):
    for table_name, columns in schema.items():
        print(f"Таблица: {table_name}")
        for column in columns:
            print(f"  - {column['name']} ({column['type']})")
        print("="*50)

def main():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    schema = fetch_schema(cursor)

    # Option 1: Visualize the schema
    visualize_schema(schema)
    
    # Option 2: Print schema in text form
    print_schema(schema)

    conn.close()

if __name__ == "__main__":
    main()
