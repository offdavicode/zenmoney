import sqlite3
import random

def seed_data():
    db_path = "zenmoney_v2.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    user_id = 1

    # 1. Limpar dados anteriores do usuário 1
    print("Limpando transações e recorrências anteriores do usuário 1...")
    cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM recurrences WHERE user_id = ?", (user_id,))

    # 2. Buscar categorias padrões e personalizadas do usuário 1
    cursor.execute("SELECT id, name, type FROM categories WHERE user_id IS NULL OR user_id = ?",(user_id,))
    categories = cursor.fetchall()

    # Mapear nome para ID
    cat_by_type = {'income': {}, 'expense': {}}
    for cid, name, ctype in categories:
        cat_by_type[ctype][name] = cid

    print("Categorias mapeadas para seeding:")
    print("Receitas:", cat_by_type['income'])
    print("Despesas:", cat_by_type['expense'])

    # 3. Criar Recorrências no banco de dados para Aluguel e Contas
    rent_cat_id = cat_by_type['expense'].get('Moradia')
    cursor.execute("""
        INSERT INTO recurrences (user_id, category_id, type, amount, description, emotion, frequency, day_of_month, start_date, end_date, next_run_date, is_active, created_at, updated_at)
        VALUES (?, ?, 'expense', 1100.00, 'Aluguel do apartamento', 'calma', 'monthly', 10, '2026-01-10', NULL, '2026-07-10', 1, '2026-01-10 00:00:00', '2026-01-10 00:00:00')
    """, (user_id, rent_cat_id))
    rent_recurrence_id = cursor.lastrowid

    bills_cat_id = cat_by_type['expense'].get('Contas Residenciais') or cat_by_type['expense'].get('Contas')
    cursor.execute("""
        INSERT INTO recurrences (user_id, category_id, type, amount, description, emotion, frequency, day_of_month, start_date, end_date, next_run_date, is_active, created_at, updated_at)
        VALUES (?, ?, 'expense', 180.00, 'Energia e Internet', 'indiferenca', 'monthly', 12, '2026-01-12', NULL, '2026-07-12', 1, '2026-01-12 00:00:00', '2026-01-12 00:00:00')
    """, (user_id, bills_cat_id))
    bills_recurrence_id = cursor.lastrowid

    # Meses passados completos para popular (Janeiro a Maio de 2026)
    past_months = [
        (2026, 1),
        (2026, 2),
        (2026, 3),
        (2026, 4),
        (2026, 5),
    ]

    created_records = 0

    # Função auxiliar para inserir transações
    def insert_tx(category_id, tx_type, amount, date_str, desc, emotion, rec_id=None, is_rec=0):
        nonlocal created_records
        cursor.execute("""
            INSERT INTO transactions (user_id, category_id, type, amount, date, description, emotion, created_at, updated_at, recurrence_id, is_recurring)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            category_id,
            tx_type,
            amount,
            date_str,
            desc,
            emotion,
            f"{date_str} 12:00:00",
            f"{date_str} 12:00:00",
            rec_id,
            is_rec
        ))
        created_records += 1

    # Popular meses anteriores
    for year, month in past_months:
        # 2 Receitas
        insert_tx(cat_by_type['income'].get('Salário'), 'income', 3200.00, f"{year}-{month:02d}-05", 'Salário mensal', 'felicidade')
        insert_tx(cat_by_type['income'].get('Freelance') or cat_by_type['income'].get('Outros recebimentos'), 'income', 650.00, f"{year}-{month:02d}-18", 'Desenvolvimento freelance', 'satisfacao')

        # 2 Despesas Recorrentes
        insert_tx(rent_cat_id, 'expense', 1100.00, f"{year}-{month:02d}-10", 'Aluguel do apartamento', 'calma', rent_recurrence_id, 1)
        insert_tx(bills_cat_id, 'expense', 180.00, f"{year}-{month:02d}-12", 'Energia e Internet', 'indiferenca', bills_recurrence_id, 1)

        # 3. Alimentação (Despesa) - Emoção: calma, satisfacao, tedio
        insert_tx(cat_by_type['expense'].get('Alimentação'), 'expense', 54.20, f"{year}-{month:02d}-03", 'Almoço Executivo', 'satisfacao')
        insert_tx(cat_by_type['expense'].get('Alimentação'), 'expense', 112.50, f"{year}-{month:02d}-15", 'Supermercado Mensal', 'calma')
        insert_tx(cat_by_type['expense'].get('Alimentação'), 'expense', 38.00, f"{year}-{month:02d}-27", 'Lanche Rápido', 'tedio')

        # 4. Transporte (Despesa) - Emoção: estresse, indiferenca
        insert_tx(cat_by_type['expense'].get('Transporte'), 'expense', 45.00, f"{year}-{month:02d}-08", 'Metrô e ônibus', 'indiferenca')
        insert_tx(cat_by_type['expense'].get('Transporte'), 'expense', 78.00, f"{year}-{month:02d}-22", 'Uber no trânsito', 'estresse')

        # 5. Lazer / Hobbies (Despesa) - Emoção: empolgacao, felicidade
        insert_tx(cat_by_type['expense'].get('Lazer') or cat_by_type['expense'].get('Hobbies'), 'expense', 140.00, f"{year}-{month:02d}-14", 'Ingresso Show / Cinema', 'empolgacao')
        insert_tx(cat_by_type['expense'].get('Hobbies') or cat_by_type['expense'].get('Lazer'), 'expense', 95.00, f"{year}-{month:02d}-25", 'Jogo Steam / Acessório', 'felicidade')

        # 6. Compras / Roupas (Despesa) - Emoção: ansiedade, frustracao
        insert_tx(cat_by_type['expense'].get('Compras') or cat_by_type['expense'].get('Outros gastos'), 'expense', 230.00, f"{year}-{month:02d}-06", 'Roupas novas', 'ansiedade')
        insert_tx(cat_by_type['expense'].get('Roupas') or cat_by_type['expense'].get('Outros gastos'), 'expense', 125.00, f"{year}-{month:02d}-20", 'Acessório eletrônico', 'frustracao')

        # 7. Saúde (Despesa) - Emoção: ansiedade, calma
        insert_tx(cat_by_type['expense'].get('Saúde'), 'expense', 150.00, f"{year}-{month:02d}-04", 'Consulta Médica', 'calma')
        insert_tx(cat_by_type['expense'].get('Saúde'), 'expense', 65.00, f"{year}-{month:02d}-16", 'Remédios Farmácia', 'ansiedade')

        # 8. Educação (Despesa) - Emoção: satisfacao, estresse
        insert_tx(cat_by_type['expense'].get('Educação'), 'expense', 320.00, f"{year}-{month:02d}-01", 'Mensalidade Curso', 'satisfacao')
        insert_tx(cat_by_type['expense'].get('Educação'), 'expense', 45.00, f"{year}-{month:02d}-19", 'Livro Acadêmico', 'estresse')

        # 9. Cuidados Pessoais (Despesa) - Emoção: calma, felicidade
        insert_tx(cat_by_type['expense'].get('Cuidados Pessoais'), 'expense', 80.00, f"{year}-{month:02d}-24", 'Corte de Cabelo / Barbearia', 'calma')

        # 10. Dívidas / Contas (Despesa) - Emoção: raiva, estresse
        insert_tx(cat_by_type['expense'].get('Dívidas'), 'expense', 200.00, f"{year}-{month:02d}-11", 'Parcela de Empréstimo', 'raiva')

        # 11. Outros Gastos - Emoção: not_specified (Não especificada)
        insert_tx(cat_by_type['expense'].get('Outros gastos') or cat_by_type['expense'].get('Contas'), 'expense', 50.00, f"{year}-{month:02d}-28", 'Despesa miúda', 'not_specified')


    # 4. Popular o mês atual de Junho/2026 até hoje (dia 15)
    curr_year, curr_month = 2026, 6

    # Salário (Receita) - felicidade
    insert_tx(cat_by_type['income'].get('Salário'), 'income', 3200.00, f"{curr_year}-{curr_month:02d}-05", 'Salário mensal', 'felicidade')

    # Aluguel (Moradia - Recorrente) - calma
    insert_tx(rent_cat_id, 'expense', 1100.00, f"{curr_year}-{curr_month:02d}-10", 'Aluguel do apartamento', 'calma', rent_recurrence_id, 1)

    # Contas (Contas Residenciais - Recorrente) - indiferenca
    insert_tx(bills_cat_id, 'expense', 180.00, f"{curr_year}-{curr_month:02d}-12", 'Energia e Internet', 'indiferenca', bills_recurrence_id, 1)

    # Dia 1: Educação - satisfacao
    insert_tx(cat_by_type['expense'].get('Educação'), 'expense', 320.00, f"{curr_year}-{curr_month:02d}-01", 'Mensalidade Curso', 'satisfacao')
    
    # Dia 3: Alimentação - tedio
    insert_tx(cat_by_type['expense'].get('Alimentação'), 'expense', 65.40, f"{curr_year}-{curr_month:02d}-03", 'Almoço Restaurante', 'tedio')

    # Dia 4: Saúde - estresse
    insert_tx(cat_by_type['expense'].get('Saúde'), 'expense', 90.00, f"{curr_year}-{curr_month:02d}-04", 'Exame Clínico', 'estresse')

    # Dia 6: Compras - ansiedade
    insert_tx(cat_by_type['expense'].get('Compras') or cat_by_type['expense'].get('Outros gastos'), 'expense', 120.00, f"{curr_year}-{curr_month:02d}-06", 'Tênis novo', 'ansiedade')

    # Dia 8: Transporte - indiferenca
    insert_tx(cat_by_type['expense'].get('Transporte'), 'expense', 45.00, f"{curr_year}-{curr_month:02d}-08", 'Abastecimento carro', 'indiferenca')

    # Dia 11: Dívidas - raiva
    insert_tx(cat_by_type['expense'].get('Dívidas'), 'expense', 200.00, f"{curr_year}-{curr_month:02d}-11", 'Tarifa Banco', 'raiva')

    # Dia 14: Lazer - empolgacao
    insert_tx(cat_by_type['expense'].get('Lazer') or cat_by_type['expense'].get('Hobbies'), 'expense', 85.00, f"{curr_year}-{curr_month:02d}-14", 'Cinema e Jantar', 'empolgacao')

    # Dia 15 (Hoje): Cuidados Pessoais - felicidade
    insert_tx(cat_by_type['expense'].get('Cuidados Pessoais'), 'expense', 60.00, f"{curr_year}-{curr_month:02d}-15", 'Corte de cabelo', 'felicidade')

    # Dia 15 (Hoje): Frustração com outra despesa de compras
    insert_tx(cat_by_type['expense'].get('Compras') or cat_by_type['expense'].get('Outros gastos'), 'expense', 45.00, f"{curr_year}-{curr_month:02d}-15", 'Reparo Urgente', 'frustracao')

    conn.commit()
    conn.close()
    
    print(f"Sucesso! Banco de dados atualizado com {created_records} transações abrangendo 13 categorias e 11 emoções distintas!")

if __name__ == "__main__":
    seed_data()
