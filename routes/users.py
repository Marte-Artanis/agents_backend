from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db, db
from dependencies import get_current_user
from models import UserUpdate, UserResponse
import auth

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_profile(
    user = Depends(get_current_user)
):
    """Retorna o perfil do usuário atual"""
    try:
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    user = Depends(get_current_user),
    _db: Session = Depends(get_db)  # renomeado para _db já que não vamos usar
):
    """Atualiza o perfil do usuário"""
    try:
        # Verificar se os novos valores são diferentes dos atuais
        current_user = db.fetch(
            "SELECT first_name, last_name, password_hash FROM users WHERE id = %s",
            [user['id']]
        )
        
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
        current_user = current_user[0]

        # Preparar campos para atualização
        update_fields = []
        params = []
        has_changes = False
        
        # Validações de senha
        if user_data.new_password:
            if not user_data.current_password:
                raise HTTPException(status_code=400, detail="Senha atual é necessária para alterar a senha")
            
            # Verifica se a senha atual está correta
            if not auth.verify_password(user_data.current_password, current_user['password_hash']):
                raise HTTPException(status_code=400, detail="Senha atual incorreta")
            
            # Verifica se a nova senha é igual à atual
            if auth.verify_password(user_data.new_password, current_user['password_hash']):
                raise HTTPException(status_code=400, detail="A nova senha não pode ser igual à senha atual")
            
            update_fields.append("password_hash = %s")
            params.append(auth.hash_password(user_data.new_password))
            has_changes = True

        # Validações de nome
        if user_data.first_name is not None and user_data.first_name != current_user['first_name']:
            update_fields.append("first_name = %s")
            params.append(user_data.first_name)
            has_changes = True
            
        if user_data.last_name is not None and user_data.last_name != current_user['last_name']:
            update_fields.append("last_name = %s")
            params.append(user_data.last_name)
            has_changes = True

        # Se não há campos para atualizar ou valores diferentes, retorna erro
        if not has_changes:
            raise HTTPException(status_code=400, detail="Nenhuma alteração detectada nos dados fornecidos")

        # Adiciona o ID do usuário aos parâmetros
        params.append(user['id'])
        
        # Executa o UPDATE
        db.execute(f"""
            UPDATE users 
            SET {", ".join(update_fields)}
            WHERE id = %s
        """, params)
        
        # Busca os dados atualizados
        updated_user = db.fetch("""
            SELECT id, first_name, last_name, email, birth_date, created_at, updated_at
            FROM users WHERE id = %s
        """, [user['id']])
        
        if not updated_user:
            raise HTTPException(status_code=500, detail="Erro ao recuperar dados atualizados")
        
        return updated_user[0]
        
    except HTTPException:
        raise
    except Exception as e:
        if "statement timeout" in str(e):
            raise HTTPException(
                status_code=503, 
                detail="Tempo limite excedido ao atualizar o usuário. Por favor, tente novamente."
            )
        raise HTTPException(
            status_code=500, 
            detail=f"Erro na operação do banco de dados: {str(e)}"
        )

@router.get("/settings")
async def get_settings(
    user = Depends(get_current_user)
):
    """Retorna as configurações do usuário"""
    try:
        # TODO: Implementar lógica de busca de configurações
        return {}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/settings")
async def update_settings(
    settings: dict,
    user = Depends(get_current_user)
):
    """Atualiza as configurações do usuário"""
    try:
        # TODO: Implementar lógica de atualização de configurações
        return settings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 