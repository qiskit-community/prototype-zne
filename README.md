<!-- SHIELDS -->
<div align="left">

  ![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-informational)
  [![Python](https://img.shields.io/badge/Python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-informational)](https://www.python.org/)
  [![Qiskit](https://img.shields.io/badge/Qiskit-%E2%89%A5%200.45.1-6133BD)](https://github.com/Qiskit/qiskit)
<br />
  [![Tests](https://github.com/qiskit-community/prototype-zne/actions/workflows/test.yml/badge.svg)](https://github.com/qiskit-community/prototype-zne/actions/workflows/test.yml)
  [![Coverage](https://coveralls.io/repos/github/qiskit-community/prototype-zne/badge.svg?branch=main)](https://coveralls.io/github/qiskit-community/prototype-zne?branch=main)
  [![Release](https://img.shields.io/github/release/qiskit-community/prototype-zne.svg?include_prereleases&label=Release)](https://github.com/qiskit-community/prototype-zne/releases)
  [![DOI](https://img.shields.io/badge/DOI-zz.nnnn/zenodo.ddddddd-informational)](https://zenodo.org/)
  [![License](https://img.shields.io/github/license/qiskit-community/prototype-zne?label=License)](LICENSE.txt)

</div>
<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="README.md">
    <img src="https://github.com/qiskit-community/prototype-zne/blob/main/docs/media/cover.png?raw=true" alt="Logo" width="300">
  </a>
  <h2 align="center">Zero Noise Extrapolation (ZNE)</h2>
</p>
<!-- QUICK LINKS -->
<!-- <p align="center">
  <a href="https://mybinder.org/">
    <img src="https://ibm.biz/BdPq3s" alt="Launch Demo" hspace="5" vspace="10">
  </a>
  <a href="https://www.youtube.com/c/qiskit">
    <img src="https://img.shields.io/badge/watch-video-FF0000.svg?style=for-the-badge&logo=youtube" alt="Watch Video" hspace="5" vspace="10">
  </a>
</p> -->


----------------------------------------------------------------------

### Table of contents

1. [About This Project](#about-this-project)
2. [About Prototypes](#about-prototypes)
3. [Deprecation Policy](#deprecation-policy)
4. [Using Quantum Services](#using-quantum-services)
5. [Acknowledgements](#acknowledgements)
6. [References](#references)
7. [License](#license)

#### For users
1. [Installation](https://github.com/qiskit-community/prototype-zne/blob/main/INSTALL.md)
2. [Tutorials](https://github.com/qiskit-community/prototype-zne/tree/main/docs/tutorials/)
3. [Reference Guide](https://github.com/qiskit-community/prototype-zne/blob/main/docs/reference_guide.md)
4. [How-tos](https://github.com/qiskit-community/prototype-zne/tree/main/docs/how_tos/)
5. [Explanations](https://github.com/qiskit-community/prototype-zne/tree/main/docs/explanations/)
6. [How to Give Feedback](https://github.com/qiskit-community/prototype-zne/blob/main/CONTRIBUTING.md#giving-feedback)

#### For developers
1. [Contribution Guidelines](https://github.com/qiskit-community/prototype-zne/blob/main/CONTRIBUTING.md)


----------------------------------------------------------------------

### About This Project

This module builds on top of the [_Estimator_ primitive official specification](https://github.com/qiskit-community/prototype-zne/blob/main/docs/tutorials/0-estimator.ipynb), providing a highly customizable _zero noise extrapolation_ (ZNE) workflow for error mitigation on expectation value calculations. This is achieved by [injecting orchestrated ZNE capabilities](https://github.com/qiskit-community/prototype-zne/blob/main/docs/tutorials/1-zne.ipynb) into an `Estimator` class of choice in two phases:

1. [Amplifying the noise](https://github.com/qiskit-community/prototype-zne/blob/main/docs/tutorials/2-noise_amplification.ipynb) introduced by the gates of input circuits.
2. Extrapolating the returned expectation values to the zero noise limit.

In principle, this prototype is compatible with any `Estimator` class as long as it implements the [`qiskit.primitives.BaseEstimator` interface](https://github.com/Qiskit/qiskit/tree/main/qiskit/primitives) (e.g. `qiskit.primitives.Estimator`, `qiskit.primitives.BackendEstimator`, `qiskit_ibm_runtime.Estimator`). Notice, however, that error mitigation techniques only make sense in the context of noisy computations; therefore using ZNE on noisless platforms (e.g. simulators), although technically possible, will not produce better results.

Furthermore, the software architecture has been devised specifically to allow users to create their custom noise amplification and extrapolation techniques, and to plug them into the overall ZNE workflow seamlessly. Libraries of pre-implemented strategies for both of these tasks are provided in the module, and external packages can easily be made to work with this tool by providing [implementations of well defined interfaces](https://github.com/qiskit-community/prototype-zne/blob/main/docs/reference_guide.md#custom-zne-strategies) for these tasks.

Before using the module for new work, users should read through the [reference guide](https://github.com/qiskit-community/prototype-zne/blob/main/docs/reference_guide.md), specifically the [current limitations](https://github.com/qiskit-community/prototype-zne/blob/main/docs/reference_guide.md#current-limitations) of the module. Demo [tutorials](https://github.com/qiskit-community/prototype-zne/tree/main/docs/tutorials) are also available as jupyter notebooks.


----------------------------------------------------------------------

### About Prototypes

Prototypes is a collaboration between developers and researchers that will give users early access to solutions from cutting-edge research in areas like error mitigation, quantum simulation, and machine learning. These software packages are built on top of, and may eventually be integrated into the Qiskit SDK. They are a contribution as part of the Qiskit community.

Check out our [landing page](https://qiskit-community.github.io/prototypes/) and [blog post](https://medium.com/qiskit/try-out-the-latest-advances-in-quantum-computing-with-ibm-quantum-prototypes-11f51124cb61) for more information!


----------------------------------------------------------------------

### Deprecation Policy

Prototypes are meant to evolve rapidly and, as such, do not follow [Qiskit's deprecation policy](https://qiskit.org/documentation/contributing_to_qiskit.html#deprecation-policy). We may occasionally make breaking changes in order to improve the user experience. When possible, we will keep old interfaces and mark them as deprecated, as long as they can co-exist with the new ones. Each substantial improvement, breaking change, or deprecation will be documented in [`CHANGELOG.md`](https://github.com/qiskit-community/prototype-zne/blob/main/CHANGELOG.md).


----------------------------------------------------------------------

### Using Quantum Services

If you are interested in using quantum services (i.e. using a real quantum computer, not a simulator) you can look at the [Qiskit Partners program](https://qiskit.org/documentation/partners/) for partner organizations that have provider packages available for their offerings.

Importantly, *[Qiskit IBM Runtime](https://qiskit.org/documentation/partners/qiskit_ibm_runtime)* is a quantum computing service and programming model that allows users to optimize workloads and efficiently execute them on quantum systems at scale; extending the existing interface in Qiskit with a set of new *primitive* programs.


----------------------------------------------------------------------

### Acknowledgements

- __Mario Motta__: for scientific insight and guidance.
- __Julien Gacon__: for providing a util function that maps gate names to the corresponding gate classes and for general discussions.
- __Derek Wang__: for suggesting new features and stress-testing the tool.

----------------------------------------------------------------------

### References

[1] Kandala, Abhinav, et al. "Extending the computational reach of a noisy superconducting quantum processor." arXiv:1805.04492(2018).

[2] Stamatopoulos, Nikitas, et al. "Option pricing using quantum computers." Quantum4 (2020): 291.

[3] LaRose, Ryan, et al. "Mitiq: A software package for error mitigation on noisy quantum computers." arXiv:2009.04417(2020).

[4] Kim, Youngseok, et al. "Scalable error mitigation for noisy quantum circuits produces competitive expectation values." arXiv:2108.09197(2021).

[5] T. Giurgica-Tiron, Y. Hindy, R. LaRose, A. Mari and W. J. Zeng, "Digital zero noise extrapolation for quantum error mitigation," 2020 IEEE International Conference on Quantum Computing and Engineering (QCE), Denver, CO, USA, 2020, pp. 306-316, doi: 10.1109/QCE49297.2020.00045.


----------------------------------------------------------------------

### License
[Apache License 2.0](https://github.com/qiskit-community/prototype-zne/blob/main/LICENSE.txt)
