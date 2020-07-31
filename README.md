# PreonLab-HTC-averaging
This simple Python script will average your PreonLab heat transfer and HTC for E-motor, engine (and everything that rotates) simulations.
This is useful if you want to do an external study of heat transfers in a third party tool.

It will automaticaly do the averaging of heat flux sensors that :
- Are linked to a sensor plane using sensor plane temperature (We want global HTCs)
- Have keyframed "behavior"

It will detect active frames and will do the averaging of all those frames.
And it will then create a CSV file for each sensor.

It will build a CSV file like :
X,Y,Z,REF_TEMP,CONV_HTC,HEAT_FLUX
-0.002783743431791663,-0.06720496714115143,-0.08070015907287598,120.0,126.87427616119385,-3730.1029357910156
-0.0025842373725026846,-0.06721598654985428,-0.08070019632577896,120.0,135.3618049621582,-3979.636215209961
-0.002783718053251505,-0.06720457971096039,-0.08050017058849335,120.0,520.2167205810547,-15294.368041992188
...

-Make sure HF sensors activity is on for the last rotation and inactive outside.
-Make sure the HF sensors are linked with MeasuredScalarValue with a reference sensor plane (for global HTCs).
-Also make sure that current_dir and scene_name are filled.
-Of course, make sure that each sensor has data (is post processed) in your PreonLab scene, at least during activity.
