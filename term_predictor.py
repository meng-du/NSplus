import neurosynth as ns
import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVR, LinearSVR
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor


dataset = ns.Dataset.load('dataset.pkl')
features = dataset.get_feature_data()  # get term frequencies, shape = (11406, 3169)
activations = dataset.get_image_data().T  # get activations, shape = (11406, 228453)
assert np.all(features.index == dataset.image_table.ids)  # make sure the ids match


# customized scoring function
def tag_accuracy(estimator, X, y):
    # TODO
    return 1.0

# regression
# linear SVR
# lsvr = GridSearchCV(
#     estimator=LinearSVR(),
#     param_grid={'C': 10.0 ** np.arange(-3, 3)},
#     scoring='r2',
#     cv=10,
#     n_jobs=-1  # use all CPUs
# )
# lsvr.fit(features, activations)  # X: shape = [n_samples, n_features], y: shape = [n_samples] or [n_samples, n_output]
# print lsvr.cv_results_
# print 'BEST SCORE', lsvr.best_score_
# print 'BEST PARAMS', lsvr.best_params_
# # rbf SVR
# svr = GridSearchCV(
#     estimator=SVR(),
#     param_grid={'gamma': 10.0 ** np.arange(-5, 2), 'C': 10.0 ** np.arange(-3, 3)},
#     scoring='r2',
#     cv=10,
#     n_jobs=-1
# )
# svr.fit(features, activations)
# print svr.cv_results_
# print 'BEST SCORE', svr.best_score_
# print 'BEST PARAMS', svr.best_params_
# random forest
# TODO CV unnecessary?
rf = GridSearchCV(
    estimator=RandomForestRegressor(),
    param_grid={'n_estimators': [20, 40, 80, 160, 800, 1600], 'max_features': [0.33, 'sqrt'],
                'min_samples_split': [3, 5, 7]},
    scoring='r2',
    cv=10,
    n_jobs=-1
)
rf.fit(features, activations)
print rf.cv_results_
print 'BEST SCORE', rf.best_score_
print 'BEST PARAMS', rf.best_params_
# TODO refit and see oob score
# Extremely Randomized Trees
et = GridSearchCV(
    estimator=ExtraTreesRegressor(),
    param_grid={'n_estimators': [20, 40, 80, 160, 800, 1600], 'max_features': [0.33],
                'min_samples_split': [3, 5, 7], 'oob_score': [True]},
    scoring='r2',
    cv=10,
    n_jobs=-1
)
et.fit(features, activations)
print et.cv_results_
print 'BEST SCORE', et.best_score_
print 'BEST PARAMS', et.best_params_
# TODO refit and see oob score
