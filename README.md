# NS+
NS+ is a [Neurosynth](www.neurosynth.org)-based tool (plus a graphical user interface) for fMRI meta-analysis. It provides a flexible interface for Neurosynth's large-scale (14371 studies), automated meta-analysis abilities, and additionally supports highly customizable forward or reverse inference analyses within any given brain region of interest.

Some of the things you could do with NS+:
- **Rank** 3000+ terms (e.g. "social", "emotion", "working memory") in any ROI based on reverse inference (posterior probability) to explore what brain functions the ROI is responsible for
- **Compare multiple terms** and get a map showing the territory where each term dominates in an ROI (battle royale!)
- Analyze, compare or rank **custom terms** in addition to existing terms in Neurosynth
- ... and more functionalities in development!

## Examples
[This document](https://github.com/MetaD/NSplus/tree/master/docs/NS+_TPJdemo.pdf) contains a demonstration of NS+ that examines the functional subdivisions of the temporoparietal junction (TPJ).

We have also published a paper where NS+ helped recognize the functional subdivisions of mPFC: [Lieberman, M. D., Straccia, M. A., Meyer, M. L., Du, M., & Tan, K. M. (2019). *Social, Self,(Situational), and Affective Processes in Medial Prefrontal Cortex (MPFC): Causal, Multivariate, and Reverse Inference Evidence.* Neuroscience & Biobehavioral Reviews.](http://www.scn.ucla.edu/pdf/Lieberman(2019)NBR.pdf)

More documentation and examples in progress...

## Installation
You can now download a beta version for MacOS [here](https://github.com/MetaD/NSplus/releases). **No need to install anything** -- just unzip it and start to use.

For Python coders: you could alternatively use NS+ as a Python package, and run analyses in Python instead of using the GUI. To install NS+ (beta) with pip: `pip install git+https://github.com/MetaD/NSplus.git`

## Contribution & Getting Help
To report a bug, request a feature, or ask a question, please [create a new issue](https://github.com/MetaD/NSplus/issues/new) or contact Meng Du <<mengdu@umich.edu>>.
