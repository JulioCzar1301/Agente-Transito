import os
import sqlite3
import json

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "database.db")
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), "question.json")

def load_questions_from_json():
    """Carrega as questões do arquivo JSON"""
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Erro: Arquivo {JSON_FILE_PATH} não encontrado!")
        return None
    except json.JSONDecodeError as e:
        print(f"Erro: Arquivo JSON inválido! {e}")
        return None

def create_database():
    db_exists = os.path.exists(DATABASE_PATH)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if not db_exists:
        print(f"Creating new database at {DATABASE_PATH}...")
        
        questions_data = load_questions_from_json()
        if not questions_data:
            print("Não foi possível carregar as questões. Criando banco vazio.")
            conn.close()
            return

        # Create categories table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
            """
        )
        print("Created 'categories' table.")

        # Create questions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                number INTEGER NOT NULL,
                type TEXT NOT NULL,
                question TEXT NOT NULL,
                alternative_a TEXT NOT NULL,
                alternative_b TEXT NOT NULL,
                alternative_c TEXT NOT NULL,
                alternative_d TEXT NOT NULL,
                correct_alternative TEXT NOT NULL CHECK (correct_alternative IN ('A', 'B', 'C', 'D')),
                photo TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
            """
        )
        print("Created 'questions' table.")

        # Create users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        print("Created 'users' table.")

        # Create user_progress table - RASTREAMENTO DE PROGRESSO
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                total_answered INTEGER DEFAULT 0,
                total_correct INTEGER DEFAULT 0,
                percentage REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (category_id) REFERENCES categories (id),
                UNIQUE(user_id, category_id)
            )
            """
        )
        print("Created 'user_progress' table.")

        # Create user_answers table - HISTÓRICO DE RESPOSTAS
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                user_answer TEXT NOT NULL CHECK (user_answer IN ('A', 'B', 'C', 'D')),
                correct_answer TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (question_id) REFERENCES questions (id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
            """
        )
        print("Created 'user_answers' table.")

        # Create todos table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        print("Created 'todos' table.")

        cursor.execute(
            """
          CREATE TABLE simulados_realizados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            categoria_name TEXT NOT NULL,
            total_questoes INTEGER NOT NULL,
            total_corretas INTEGER NOT NULL,
            total_erradas INTEGER NOT NULL,
            percentual_acerto REAL NOT NULL,
            tempo_realizacao INTEGER,
            data_realizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
         )
        """
        )

        # Insert categories from JSON
        categories = []
        category_map = {}
        
        if "prova" in questions_data:
            prova = questions_data["prova"]
            
            unique_types = set()
            for questao in prova["questoes"]:
                unique_types.add(questao["tipo"])
            
            for tipo in unique_types:
                categories.append((tipo, f"Prova - {tipo}"))
        
        cursor.executemany(
            "INSERT INTO categories (name, description) VALUES (?, ?)", categories
        )
        print(f"Inserted {len(categories)} categories.")

        # Get category IDs
        cursor.execute("SELECT id, name FROM categories")
        category_rows = cursor.fetchall()
        category_map = {name: id for id, name in category_rows}

        # Insert questions from JSON
        questions_to_insert = []
        
        if "prova" in questions_data:
            prova = questions_data["prova"]
            
            for questao in prova["questoes"]:
                category_name = questao["tipo"]
                category_id = category_map[category_name]
                foto = questao.get("foto")
                
                questions_to_insert.append((
                    category_id,
                    questao["numero"],
                    questao["tipo"],
                    questao["pergunta"],
                    questao["alternativas"]["A"],
                    questao["alternativas"]["B"],
                    questao["alternativas"]["C"],
                    questao["alternativas"]["D"],
                    questao["correta"],
                    foto
                ))

        cursor.executemany(
            """INSERT INTO questions 
            (category_id, number, type, question, alternative_a, alternative_b, alternative_c, alternative_d, correct_alternative, photo) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
            questions_to_insert
        )
        print(f"Inserted {len(questions_to_insert)} questions.")

        # Insert dummy users
        dummy_users = [
            ("alice", "alice@example.com"),
            ("bob", "bob@example.com"),
            ("charlie", "charlie@example.com"),
        ]
        cursor.executemany(
            "INSERT INTO users (username, email) VALUES (?, ?)", dummy_users
        )
        print(f"Inserted {len(dummy_users)} dummy users.")

        conn.commit()
        print("Database created and populated successfully.")
        
        # Mostrar estatísticas
        cursor.execute("SELECT COUNT(*) FROM questions")
        total_questions = cursor.fetchone()[0]
        cursor.execute("SELECT name, COUNT(*) FROM categories c JOIN questions q ON c.id = q.category_id GROUP BY c.name")
        category_stats = cursor.fetchall()
        
        print(f"\n--- Estatísticas ---")
        print(f"Total de questões: {total_questions}")
        for category, count in category_stats:
            print(f"{category}: {count} questões")
            
    else:
        print(f"Database already exists at {DATABASE_PATH}. No changes made.")

    conn.close()

def registrar_resposta_usuario(user_id: int, question_id: int, category_id: int, resposta_usuario: str, resposta_correta: str) -> bool:
    """Registra a resposta do usuário e atualiza o progresso"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        is_correct = resposta_usuario == resposta_correta
        
        # Inserir resposta
        cursor.execute(
            """INSERT INTO user_answers (user_id, question_id, category_id, user_answer, correct_answer, is_correct)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, question_id, category_id, resposta_usuario, resposta_correta, is_correct)
        )
        
        # Atualizar ou criar progresso do usuário por categoria
        cursor.execute(
            "SELECT id, total_answered, total_correct FROM user_progress WHERE user_id = ? AND category_id = ?",
            (user_id, category_id)
        )
        progress = cursor.fetchone()
        
        if progress:
            # Atualizar
            progress_id, total_answered, total_correct = progress
            new_total = total_answered + 1
            new_correct = total_correct + (1 if is_correct else 0)
            percentage = (new_correct / new_total) * 100 if new_total > 0 else 0
            
            cursor.execute(
                """UPDATE user_progress 
                   SET total_answered = ?, total_correct = ?, percentage = ?, last_updated = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (new_total, new_correct, percentage, progress_id)
            )
        else:
            # Criar novo
            new_total = 1
            new_correct = 1 if is_correct else 0
            percentage = (new_correct / new_total) * 100
            
            cursor.execute(
                """INSERT INTO user_progress (user_id, category_id, total_answered, total_correct, percentage)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, category_id, new_total, new_correct, percentage)
            )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao registrar resposta: {e}")
        return False

def obter_progresso_usuario(user_id: int) -> list:
    """Obtém o progresso do usuário em todas as categorias"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT c.name, c.description, up.total_answered, up.total_correct, up.percentage, up.last_updated
               FROM user_progress up
               JOIN categories c ON up.category_id = c.id
               WHERE up.user_id = ?
               ORDER BY up.percentage DESC""",
            (user_id,)
        )
        
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Erro ao obter progresso: {e}")
        return []

def test_database():
    """Função para testar se os dados foram inseridos corretamente"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("\n--- Testando Banco de Dados ---")
    
    # Verificar categorias
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    print("Categorias:")
    for cat in categories:
        print(f"  {cat}")
    
    # Verificar algumas questões
    cursor.execute("SELECT number, type, question, correct_alternative FROM questions LIMIT 5")
    questions = cursor.fetchall()
    print("\nPrimeiras 5 questões:")
    for q in questions:
        print(f"  {q}")
    
    conn.close()

if __name__ == "__main__":
    create_database()
    test_database()