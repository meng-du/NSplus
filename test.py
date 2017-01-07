# import neurosynth as ns
from neurosynth import Dataset
from neurosynth import meta, decode, network

# ns.dataset.download(path='.', unpack=True)
# dataset = Dataset('current_data/database.txt')
# dataset.add_features('current_data/features.txt')
# dataset.save('current_data/dataset.pkl')
dataset = Dataset.load('current_data/dataset.pkl')

ids = dataset.get_studies(features='emo*', frequency_threshold=0.05)
ma = meta.MetaAnalysis(dataset, ids)
ma.save_results('./emotion', 'emotion')


recog_ids = dataset.get_studies(features='recognition', frequency_threshold=0.05)
print "Found %d studies of recognition" % len(recog_ids)

recoll_ids = dataset.get_studies(features='recollection', frequency_threshold=0.05)
print "Found %d studies of recollection" % len(recoll_ids)

ma = meta.MetaAnalysis(dataset, recog_ids, recoll_ids)
ma.save_results('./contrast', 'recognition_vs_recollection')