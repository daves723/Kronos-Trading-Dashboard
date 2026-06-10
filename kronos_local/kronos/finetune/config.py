import os
import torch


def auto_detect_device() -> str:
    """Auto-detect best available device for training."""
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def auto_detect_world_size() -> int:
    """Detect number of GPUs for DDP, or 1 for single-device training."""
    if torch.cuda.is_available():
        return torch.cuda.device_count()
    return 1


class Config:
    """
    Configuration class for the entire project.
    All paths support env-var override via KRONOS_<ATTR> (uppercase).
    """

    def __init__(self):
        # =================================================================
        # Data & Feature Parameters
        # =================================================================
        self.qlib_data_path = os.environ.get(
            "KRONOS_QLIB_DATA_PATH", "~/.qlib/qlib_data/cn_data")
        self.instrument = os.environ.get("KRONOS_INSTRUMENT", "csi300")

        # Overall time range for data loading from Qlib.
        self.dataset_begin_time = "2011-01-01"
        self.dataset_end_time = '2025-06-05'

        # Sliding window parameters for creating samples.
        self.lookback_window = 90
        self.predict_window = 10
        self.max_context = 512

        # Features to be used from the raw data.
        self.feature_list = ['open', 'high', 'low', 'close', 'vol', 'amt']
        self.time_feature_list = ['minute', 'hour', 'weekday', 'day', 'month']

        # =================================================================
        # Dataset Splitting & Paths
        # =================================================================
        self.train_time_range = ["2011-01-01", "2022-12-31"]
        self.val_time_range = ["2022-09-01", "2024-06-30"]
        self.test_time_range = ["2024-04-01", "2025-06-05"]
        self.backtest_time_range = ["2024-07-01", "2025-06-05"]

        self.dataset_path = "./data/processed_datasets"

        # =================================================================
        # Training Hyperparameters
        # =================================================================
        self.clip = 5.0
        self.epochs = 30
        self.log_interval = 100
        self.batch_size = 50

        self.n_train_iter = 2000 * self.batch_size
        self.n_val_iter = 400 * self.batch_size

        self.tokenizer_learning_rate = 2e-4
        self.predictor_learning_rate = 4e-5
        self.accumulation_steps = 1

        self.adam_beta1 = 0.9
        self.adam_beta2 = 0.95
        self.adam_weight_decay = 0.1
        self.seed = 100

        # =================================================================
        # Checkpoint & Resume
        # =================================================================
        self.resume_from_checkpoint = (
            os.environ.get("KRONOS_RESUME", "true").lower() in ("1", "true", "yes"))
        self.save_every_n_epochs = int(os.environ.get("KRONOS_SAVE_EVERY", "5"))
        self.keep_last_n_checkpoints = int(os.environ.get("KRONOS_KEEP_CHECKPOINTS", "3"))

        # =================================================================
        # Device & Distributed
        # =================================================================
        self.device = os.environ.get("KRONOS_DEVICE", auto_detect_device())
        self.world_size = int(os.environ.get("KRONOS_WORLD_SIZE", "0")) or auto_detect_world_size()

        # =================================================================
        # Experiment Logging & Saving
        # =================================================================
        self.use_comet = os.environ.get("COMET_API_KEY") is not None
        self.comet_config = {
            "api_key": os.environ.get("COMET_API_KEY", ""),
            "project_name": os.environ.get("COMET_PROJECT", "Kronos-Finetune-Demo"),
            "workspace": os.environ.get("COMET_WORKSPACE", ""),
        }
        if self.use_comet and not self.comet_config["api_key"]:
            raise ValueError("COMET_API_KEY env var required when use_comet is True")
        self.comet_tag = 'finetune_demo'
        self.comet_name = 'finetune_demo'

        self.save_path = "./outputs/models"
        self.tokenizer_save_folder_name = 'finetune_tokenizer_demo'
        self.predictor_save_folder_name = 'finetune_predictor_demo'
        self.backtest_save_folder_name = 'finetune_backtest_demo'
        self.backtest_result_path = "./outputs/backtest_results"

        # =================================================================
        # Model & Checkpoint Paths
        # =================================================================
        self.pretrained_tokenizer_path = os.environ.get(
            "KRONOS_PRETRAINED_TOKENIZER", "path/to/your/Kronos-Tokenizer-base")
        self.pretrained_predictor_path = os.environ.get(
            "KRONOS_PRETRAINED_PREDICTOR", "path/to/your/Kronos-small")

        self.finetuned_tokenizer_path = \
            f"{self.save_path}/{self.tokenizer_save_folder_name}/checkpoints/best_model"
        self.finetuned_predictor_path = \
            f"{self.save_path}/{self.predictor_save_folder_name}/checkpoints/best_model"

        # =================================================================
        # Backtesting Parameters
        # =================================================================
        self.backtest_n_symbol_hold = 50
        self.backtest_n_symbol_drop = 5
        self.backtest_hold_thresh = 5
        self.inference_T = 0.6
        self.inference_top_p = 0.9
        self.inference_top_k = 0
        self.inference_sample_count = 5
        self.backtest_batch_size = 1000
        self.backtest_benchmark = self._set_benchmark(self.instrument)

    def _set_benchmark(self, instrument):
        dt_benchmark = {
            'csi800': "SH000906",
            'csi1000': "SH000852",
            'csi300': "SH000300",
        }
        if instrument in dt_benchmark:
            return dt_benchmark[instrument]
        else:
            raise ValueError(f"Benchmark not defined for instrument: {instrument}")
