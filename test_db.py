from database import db

print("Testando conexão com o banco...")
tables = db.test_connection()

if tables:
    print("\nConexão bem sucedida!")
else:
    print("\nNenhuma tabela encontrada no schema atual") 