import logging

def configurar_logging():
    """Configura o sistema de logging da aplicação."""
    
    log_filename = "log.log"

    # Configuração
    logging.basicConfig(
        # Ajuste para DEBUG ou INFO conforme a necessidade de detalhe
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # O logger principal é opcional, mas útil para mensagens globais
    global_logger = logging.getLogger(__name__) 
    global_logger.info("Sistema de logging inicializado no mvp.py.")
    
    # Retorne o logger global para uso imediato no mvp.py, se desejar
    return global_logger