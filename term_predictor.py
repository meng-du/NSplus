import neurosynth as ns
import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVR, LinearSVR

dataset = ns.Dataset.load('current_data/dataset.pkl')
features = dataset.get_feature_data()  # get term frequencies, shape = (11406, 3169)
activations = dataset.get_image_data().T  # get activations, shape = (11406, 228453)
assert np.all(features.index == dataset.image_table.ids)  # make sure the ids match


# customized scoring function
def tag_accuracy(estimator, X, y):
    # TODO
    return 1.0

# rbf SVR
# svr = GridSearchCV(
#     estimator=SVR(),
#     param_grid={'gamma': 10.0 ** np.arange(-5, 2), 'C': 10.0 ** np.arange(-3, 3)},
#     scoring='r2',
#     cv=10,
#     n_jobs=-1  # use all CPUs
# )
# linear SVR
lsvr = GridSearchCV(
    estimator=LinearSVR(),
    param_grid={'C': 10.0 ** np.arange(-3, 3), 'dual': [False], 'epsilon': [0], 'verbose': [10]},
    scoring='r2',
    cv=10,
    n_jobs=-1
)
lsvr.fit(features, activations)  # X: shape = [n_samples, n_features], y: shape = [n_samples] or [n_samples, n_output]

# Random Forest
