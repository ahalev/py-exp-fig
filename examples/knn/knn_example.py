import pandas as pd

from sklearn import datasets
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from expfig import Config
from logging import getLogger


DEFAULT_CONFIG = 'knn_example_default_config.yaml'
logger = getLogger(__name__)


class KNNExample:
    def __init__(self, config=None):
        self.config = Config(config=config, default=DEFAULT_CONFIG)
        self.dataset = self.load_data()
        self.model = self.load_model()

    @staticmethod
    def load_data():
        """
        Load the iris dataset from scikit-learn.
        """
        return datasets.load_iris()

    def load_model(self):
        """
        Load a simple KNN Classifier with parameters from our Config.
        """
        hyperparams = self.config.hyperparams

        return KNeighborsClassifier(
            n_neighbors=hyperparams.n_neighbors,
            weights=hyperparams.weights,
            p=hyperparams.p
        )

    def train_and_evaluate(self):
        """
        Train and evaluate a simple KNN model.
        """
        X, y = self.dataset.data, self.dataset.target
        X_train, X_test, y_train, y_test = self._train_test_split(X, y)

        self._train_model(X_train, y_train)

        report = self._evaluate_model(X_test, y_test)
        self._save_report_and_config(report)

        return report

    def _train_test_split(self, X, y):
        test_size = self.config.train_test_split.test_size
        return train_test_split(X, y, test_size=test_size)

    def _train_model(self, X, y):
        return self.model.fit(X, y)

    def _evaluate_model(self, X, y):
        y_pred = self.model.predict(X)
        report = classification_report(y, y_pred, target_names=self.dataset.target_names, output_dict=True)
        return pd.DataFrame(report)

    def _save_report_and_config(self, report):
        logging_config = self.config.logging
        log_dir = self.config.serialize_to_dir(logging_config.log_dir, with_default=True)
        report_file = f'{log_dir}/{logging_config.report_fname}'

        report.to_csv(report_file)


if __name__ == '__main__':

    # Run with the default config:
    KNNExample().train_and_evaluate()

    # Run with more neighbors in the knn model, use distance-based weights, and log to a different directory:
    config = {
        'hyperparams.n_neighbors': 10,
        'hyperparams.weights': 'distance',
        'logging.log_dir': 'knn_example_10_neighbors_logs'
    }
    KNNExample(config).train_and_evaluate()

    # Same as the above, but with the config as a nested dictionary and a slightly different log directory:
    config = {
        'hyperparams': {'n_neighbors': 10, 'weights': 'distance'},
        'logging': {'log_dir': 'knn_example_10_neighbors_logs_version_2'}
    }
    KNNExample(config).train_and_evaluate()

