import neurosynth as ns
import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVR, LinearSVR
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
import os
import logging

os.environ["JOBLIB_TEMP_FOLDER"] = '/u/scratch2/m/mengdu/'

# logging
logging.basicConfig(filename='results.log', level=logging.INFO, format='%(asctime)s %(message)s')

# dataset = ns.Dataset(filename='current_data/database.txt')#, masker='BA10_d1_mid_ventral.nii')
# dataset.add_features('current_data/features.txt')
dataset.save('current_data/dataset.pkl')
quit()
dataset = ns.Dataset.load('current_data/dataset.pkl')  #ba10mv_
features = dataset.get_feature_data()  # get term frequencies, shape = (11406, 3169)
activations = dataset.get_image_data().T  # get activations, shape = (11406, 228453)
assert np.all(features.index == dataset.image_table.ids)  # make sure the ids match
logging.info('Neurosynth database loaded')


# customized scoring function
def tag_accuracy(estimator, X, y):
    # TODO
    return 1.0

# regression
# linear SVR
lsvr = GridSearchCV(
    estimator=LinearSVR(),
    param_grid={'C': 10.0 ** np.arange(-3, 3)},
    scoring='r2',
    cv=10,
    n_jobs=-1,  # use all CPUs
    verbose=2
)
lsvr.fit(features, activations)  # X: shape = [n_samples, n_features], y: shape = [n_samples] or [n_samples, n_output]
print '\n-------------'
print lsvr.cv_results_
print '-------------\n'
logging.info(['BEST LSVR SCORE', lsvr.best_score_])
logging.info(['BEST LSVR PARAMS', lsvr.best_params_])
# rbf SVR
svr = GridSearchCV(
    estimator=SVR(),
    param_grid={'gamma': 10.0 ** np.arange(-5, 2), 'C': 10.0 ** np.arange(-3, 3)},
    scoring='r2',
    cv=10,
    n_jobs=-1,
    verbose=2
)
svr.fit(features, activations)
print '\n-------------'
print svr.cv_results_
print '-------------\n'
logging.info(['BEST SVR SCORE', svr.best_score_])
logging.info(['BEST SVR PARAMS', svr.best_params_])
# # random forest
# # TODO CV unnecessary for rf?
# rf = GridSearchCV(
#     estimator=RandomForestRegressor(),
#     param_grid={'n_estimators': [20, 40, 80, 160, 800, 1600], 'max_features': [0.33, 'sqrt'],
#                 'min_samples_split': [3, 5, 7]},
#     scoring='r2',
#     cv=10,
#     n_jobs=-1,
#     verbose=2
# )
# rf.fit(features, activations)
# print '\n-------------'
# print rf.cv_results_
# print '-------------\n'
# logging.info(['BEST RF SCORE', rf.best_score_])
# logging.info(['BEST RF PARAMS', rf.best_params_])
# # TODO refit and see oob score
# # Extremely Randomized Trees
# et = GridSearchCV(
#     estimator=ExtraTreesRegressor(),
#     param_grid={'n_estimators': [20, 40, 80, 160, 800, 1600], 'max_features': [0.33],
#                 'min_samples_split': [3, 5, 7], 'oob_score': [True]},
#     scoring='r2',
#     cv=10,
#     n_jobs=-1,
#     verbose=2
# )
# et.fit(features, activations)
# print '\n-------------'
# print et.cv_results_
# print '-------------\n'
# logging.info(['BEST ET SCORE', et.best_score_])
# logging.info(['BEST ET PARAMS', et.best_params_])
# TODO refit and see oob score
# importances = forest.feature_importances_
# std = np.std([tree.feature_importances_ for tree in forest.estimators_],
#              axis=0)
# indices = np.argsort(importances)[::-1]
