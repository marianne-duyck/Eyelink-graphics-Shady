# Eyelink-graphics-Shady

Module that implements interaction with Eyelink eyetracker (graphics for calibration) for [Shady](https://shady.readthedocs.io/en/release/), a python toolkit for visual stimuli display.

To use the demo on Mac OS or Linux ```python -m Shady CalibrationGraphicsShady.py```, similarly on these systems if you use it in any code:
```python -m Shady whateverCode.py```

On Windows, just make sure the World is threaded (argument ```threaded=True``` at the instantiation of the World) and simply run ```python CalibrationGraphicsShady.py```

Tested on Mac OS 10.15, Eyelink 1000+ (Eyelink Developpers' Kit 2.1.1), Shady 1.13.0, pylink (SR Research) for python 3.6.13 and on Windows 10 python 3.8.8

