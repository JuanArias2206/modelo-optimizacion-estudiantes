"""
Utilidades generales del proyecto
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import json
from datetime import datetime


def setup_logging(log_dir: str = "logs", debug_dir: str = "debug_logs") -> logging.Logger:
    """Configura logging para toda la aplicación"""
    
    Path(log_dir).mkdir(exist_ok=True)
    Path(debug_dir).mkdir(exist_ok=True)
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Handler para logs normales
    log_file = Path(log_dir) / f"modelo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Handler para debug
    debug_file = Path(debug_dir) / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    dh = logging.FileHandler(debug_file)
    dh.setLevel(logging.DEBUG)
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    dh.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(dh)
    
    return logger


def save_results_json(results_dict: dict, output_file: str) -> None:
    """Guarda resultados en JSON"""
    with open(output_file, 'w') as f:
        json.dump(results_dict, f, indent=2, default=str)


def load_results_json(input_file: str) -> dict:
    """Carga resultados desde JSON"""
    with open(input_file, 'r') as f:
        return json.load(f)
