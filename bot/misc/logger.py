import logging

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
