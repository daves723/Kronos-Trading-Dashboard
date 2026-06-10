__version__ = "0.2.0"

from .kronos import KronosTokenizer, Kronos, KronosPredictor

model_dict = {
    'kronos_tokenizer': KronosTokenizer,
    'kronos': Kronos,
    'kronos_predictor': KronosPredictor,
}


def get_model_class(model_name):
    if model_name in model_dict:
        return model_dict[model_name]
    else:
        import logging
        logging.getLogger("kronos").warning("Model %s not found", model_name)
        raise NotImplementedError


