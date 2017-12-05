import neurosynth as ns
import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVR, LinearSVR
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA, KernelPCA
import os
import logging

os.environ["JOBLIB_TEMP_FOLDER"] = '/u/scratch2/m/mengdu/'

# logging
# logging.basicConfig(filename='svr_results.log', level=logging.INFO, format='%(asctime)s %(message)s')

# dataset = ns.Dataset(filename='database.txt', masker='BA10_d1_mid_anterior.nii')
# dataset.add_features('features.txt')
# dataset.save('ba10ma_dataset.pkl')
# quit()
dataset = ns.Dataset.load('ba10mv_dataset.pkl')
term_frequencies = dataset.get_feature_data(features='reward')  # shape = (11406,)
activations = dataset.get_image_data().T  # shape = (11406, 228453)
assert np.all(term_frequencies.index == dataset.image_table.ids)  # make sure the ids match
logging.info('Neurosynth database loaded')


# customized scoring function
def tag_accuracy(estimator, X, y):
    # TODO
    return 1.0


# regression
# linear SVR
lsvr_pipe = Pipeline([('reduce_dim', KernelPCA()), ('regression', LinearSVR())])
lsvr_grid = {'reduce_dim__n_components': [5, 10, 30, 70, 120],
             'reduce_dim__svd_solver': ['auto', 'randomized'],   # PCA
             # 'reduce_dim__kernel': ['linear', 'poly', 'rbf'],    # KernelPCA
             # 'reduce_dim__degree': np.arange(2, 6),              # KernelPCA
             # 'reduce_dim__gamma': 10.0 ** np.arange(-5, 3),      # KernelPCA
             'regression__C': 10.0 ** np.arange(-3, 3)}
lsvr = GridSearchCV(
    estimator=lsvr_pipe,
    param_grid=lsvr_grid,
    scoring='r2',
    cv=10,
    n_jobs=-1,  # use all CPUs
    verbose=2
)
lsvr.fit(activations, term_frequencies)  # X: shape = [n_samples, n_features], y: shape = [n_samples] or [n_samples, n_output]
print '\n-------------'
print lsvr.cv_results_
print '-------------\n'
logging.info(['BEST LSVR SCORE', lsvr.best_score_])
logging.info(['BEST LSVR PARAMS', lsvr.best_params_])
# rbf SVR
# svr_pipe = Pipeline([('reduce_dim', PCA()), ('regression', SVR())])
# svr_grid = {'reduce_dim__n_components': [5, 10, 30, 70, 120],
#             'reduce_dim__svd_solver': ['auto', 'randomized'],   # PCA
#             'regression__gamma': 10.0 ** np.arange(-5, 3),
#             'regression__C': 10.0 ** np.arange(-3, 3)}
# svr = GridSearchCV(
#     estimator=svr_pipe,
#     param_grid=svr_grid,
#     scoring='r2',
#     cv=10,
#     n_jobs=-1,
#     verbose=2
# )
# svr.fit(activations, term_frequencies)
# print '\n-------------'
# print svr.cv_results_
# print '-------------\n'
# logging.info(['BEST SVR SCORE', svr.best_score_])
# logging.info(['BEST SVR PARAMS', svr.best_params_])
# # random forest
# # TODO CV unnecessary for rf?
# rf_pipe = Pipeline([('reduce_dim', PCA()), ('regression', RandomForestRegressor())])
# rf_grid = {'reduce_dim__n_components': [5, 10, 30, 70, 120],
#            'reduce_dim__svd_solver': ['auto', 'randomized'],   # PCA
#            'regression__n_estimators': [20, 40, 80, 160, 800, 1600],
#            'regression__max_features': [0.33, 'sqrt'],
#            'regression__min_samples_split': [0.99, 2, 5]}
# rf = GridSearchCV(
#     estimator=rf_pipe,
#     param_grid=rf_grid,
#     scoring='r2',
#     cv=10,
#     n_jobs=-1,
#     verbose=2
# )
# rf.fit(activations, term_frequencies)
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
# et.fit(activations, term_frequencies)
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
