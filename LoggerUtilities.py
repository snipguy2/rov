import logging

def create_file_logger(name:str, log_filename:str, format_string:str, level:int=logging.DEBUG):
    logger = logging.getLogger(name)
    handler = logging.FileHandler(log_filename)
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    logger.addHandler(handler)
    return logger

def create_stream_logger(name:str, format_string: str, level:str):
    logger = logging.getLogger(name)
    formatter = logging.Formatter(format_string)
    handler = logging.Handler(level)
    logger.addHandler(handler)